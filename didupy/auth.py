from types import SimpleNamespace
from typing import Optional, Mapping, Any, Iterable, Union
from urllib.parse import urljoin, urlsplit, parse_qsl

import aiohttp
from aiohttp.client import (
    Fingerprint,
    ClientTimeout,
    SSLContext,  # type: ignore
)
from aiohttp.helpers import sentinel
from aiohttp.typedefs import StrOrURL, LooseCookies, LooseHeaders

from .config import (
    CLIENT_ID,
    REDIRECT_URI,
    SCOPE,
    CODE_CHALLENGE_METHOD,
    MOBILE_CLIENT_ID,
)
from .utils import generate_22byte_b64_string, get_pkce_pair, DidUPyResponse
from .errors import DidUPyError


class ArgoLoginHandler:
    """
    A handler for managing the OAuth login process with Argo didUP.

    OpenID Configuration: https://auth.portaleargo.it/.well-known/openid-configuration
    """

    BASE_URL1 = "https://auth.portaleargo.it/oauth2/"
    BASE_URL2 = "https://www.portaleargo.it/auth"

    def __init__(self, client):
        from .client import DidUPClient

        self.client: DidUPClient = client

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Optional[dict] = None,  # pylint: disable=redefined-outer-name
        cookies: Optional[LooseCookies] = None,
        headers: Optional[LooseHeaders] = None,
        skip_auto_headers: Optional[Iterable[str]] = None,
        compress: Optional[str] = None,
        chunked: Optional[bool] = None,
        raise_for_status: bool = True,
        read_until_eof: bool = True,
        proxy: Optional[StrOrURL] = None,
        timeout: Union[ClientTimeout, object] = sentinel,
        verify_ssl: Optional[bool] = None,
        fingerprint: Optional[bytes] = None,
        ssl_context: Optional[SSLContext] = None,
        ssl: Optional[Union[SSLContext, bool, Fingerprint]] = None,
        proxy_headers: Optional[LooseHeaders] = None,
        trace_request_ctx: Optional[SimpleNamespace] = None,
        read_bufsize: Optional[int] = None,
    ) -> DidUPyResponse:
        """
        Make an HTTP request for authentication.
        """
        if not endpoint.startswith(self.BASE_URL1) and not endpoint.startswith(
            self.BASE_URL2
        ):
            # NOTE: assuming it's BASE_URL1 because most endpoints are there
            endpoint = urljoin(self.BASE_URL1, endpoint.lstrip("/"))

        if method not in ["GET", "POST"]:
            raise ValueError("Method must be 'GET' or 'POST'")
        elif method == "GET":
            params = params or {}
            params["client_id"] = CLIENT_ID  # type: ignore
        elif method == "POST":
            if json:
                json["client_id"] = CLIENT_ID
            else:
                data = data or {}
                data["client_id"] = CLIENT_ID

        async with self.client.session.request(
            method,
            endpoint,
            params=params,
            data=data,
            json=json,
            cookies=cookies,
            headers=headers,
            skip_auto_headers=skip_auto_headers,
            compress=compress,
            chunked=chunked,
            raise_for_status=False,
            read_until_eof=read_until_eof,
            proxy=proxy,
            timeout=timeout,
            verify_ssl=verify_ssl,  # type: ignore
            fingerprint=fingerprint,  # type: ignore
            ssl_context=ssl_context,  # type: ignore
            ssl=ssl,
            proxy_headers=proxy_headers,
            trace_request_ctx=trace_request_ctx,
            read_bufsize=read_bufsize,
        ) as response:
            if raise_for_status:
                response.raise_for_status()

            try:
                content = await response.json()
            except aiohttp.ContentTypeError:
                content = (await response.content.read()).decode()

            return (content, response)

    async def oauth2_login(self, code_challenge: str = "") -> DidUPyResponse:
        return await self.request(
            "GET",
            "auth",
            params={
                "response_type": "code",
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "scope": SCOPE,
                "prompt": "login",
                "state": generate_22byte_b64_string(),
                "nonce": generate_22byte_b64_string(),
                "code_challenge": code_challenge,
                "code_challenge_method": CODE_CHALLENGE_METHOD,
            },
        )

    async def sso_login(
        self, login_challenge: str, school_code: str, username: str, password: str
    ) -> DidUPyResponse:
        return await self.request(
            "POST",
            "https://www.portaleargo.it/auth/sso/login",
            data={
                "challenge": login_challenge,
                "famiglia_customer_code": school_code,
                "username": username,
                "password": password,
                "login": True,
                "prefill": False,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    async def mobile_login(self, token: str) -> DidUPyResponse:
        ret, resp = await self.request(
            "POST",
            "https://www.portaleargo.it/appfamiglia/api/rest/login",
            headers={
                "Argo-Client-Version": self.client.app_version,
                "Authorization": f"Bearer {token}",
                "X-Cod-Min": "",
                "X-Date-Exp-Auth": "9999-12-31 23:59:59.000",
            },
            json={
                "lista-opzioni-notifiche": "{}",
                "lista-x-auth-token": "[]",
                "clientID": MOBILE_CLIENT_ID,
            },
        )
        if resp.status != 200:
            raise DidUPyError(f"Mobile login failed: {resp.status}")

        return (ret, resp)

    async def login(
        self, school_code: str, username: str, password: str
    ) -> tuple[dict, dict]:
        verifier, challenge = get_pkce_pair()

        _, resp1 = await self.oauth2_login(challenge)
        if resp1.status != 200:
            raise DidUPyError(f"Failed to initiate OAuth2 login: {resp1.status}")

        query_params = dict(parse_qsl(urlsplit(str(resp1.url)).query))
        challenge = query_params.get("login_challenge")

        if not challenge:
            raise DidUPyError("Login challenge not found in the response URL")

        try:
            _, resp2 = await self.sso_login(challenge, school_code, username, password)
            if resp2.status != 200:
                raise DidUPyError(f"Login failed: {resp2.status}")

            url = str(resp2.url)
        except aiohttp.NonHttpUrlClientError as e:
            # all good, we expect a redirect to a custom scheme URL
            url = e.args[0]
            if not url.startswith(REDIRECT_URI):
                raise DidUPyError(f"Unexpected redirect URL: {url}") from e

        code = dict(
            [part.split("=") for part in urlsplit(url).query.split("&") if "=" in part]
        ).get("code")

        if not code:
            raise DidUPyError("Authorization code not found after SSO login")

        token, resp3 = await self.request(
            "POST",
            "token",
            data={
                "client_id": CLIENT_ID,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        if resp3.status != 200:
            raise DidUPyError(f"Token exchange failed: {resp3.status}")

        # print(token)
        return (token, (await self.mobile_login(token["access_token"]))[0])  # type: ignore
