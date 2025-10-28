from types import SimpleNamespace
from typing import Optional, Mapping, Any, Iterable, Union, Self
from urllib.parse import urljoin, urlsplit
from datetime import datetime, timedelta
from warnings import warn
from asyncio import AbstractEventLoop

import aiohttp
from aiohttp.client import (
    Fingerprint,
    ClientTimeout,
    SSLContext,  # type: ignore
)
from aiohttp.helpers import sentinel
from aiohttp.typedefs import StrOrURL, LooseCookies, LooseHeaders
from pytz import timezone

from .config import ARGO_APP_VERSION
from .utils import DidUPyResponse
from .auth import ArgoLoginHandler
from .errors import ResponseError
from .me import Me
from .endpoints import Endpoints


class DidUPClient:
    """
    A client for interacting with the Argo didUP API.


    OpenID Configuration: https://auth.portaleargo.it/.well-known/openid-configuration

    """

    BASE_URL = "https://www.portaleargo.it/appfamiglia/api/rest/"

    def __init__(
        self,
        school_code: str,
        username: str,
        password: str,
        app_version: str = ARGO_APP_VERSION,
        loop: Optional[AbstractEventLoop] = None,
    ):
        self._session = None
        self.school_code = school_code
        self.username = username
        self.password = password
        self.__login_handler = None
        self.__token = None
        self.__refresh_token = None
        self.__login_response = None
        self.__expires_in = None
        self.__logged_in_at = None
        self.__me = None
        self.app_version = app_version
        self.__endpoints = None
        self.loop = loop

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(loop=self.loop)
        return self._session

    @property
    def endpoints(self) -> Endpoints:
        if self.__endpoints is None:
            raise ValueError("Not logged in. Call 'login()' first.")

        return self.__endpoints

    @property
    def __login(self):
        if self.__login_handler is None:

            self.__login_handler = ArgoLoginHandler(self)
        return self.__login_handler

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        self.__endpoints = None
        self.__me = None

    async def __aenter__(self):
        await self.session.__aenter__()
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.__aexit__(exc_type, exc, tb)
        await self.close()

    async def __await_login(self) -> Self:
        await self.login()
        return self

    def __await__(self):
        return self.__await_login().__await__()

    def __del__(self):
        if self.__endpoints or self.__me:
            warn(
                "didUPy not closed. Did you forget to call 'close()' or use a context manager?",
                ResourceWarning,
                stacklevel=2,
                source=self,
            )

    @property
    def me(self) -> Me:
        if self.__me is None:
            raise ValueError("Not logged in. Call 'login()' first.")

        return self.__me

    async def login(self, handle_exc=False) -> bool:
        try:
            token, mobile_token = await self.__login.login(
                school_code=self.school_code,
                username=self.username,
                password=self.password,
            )
            # TODO: use the refresh token
            self.__login_response = token
            self.__token = token.get("access_token")
            self.__refresh_token = token.get("refresh_token")
            self.__expires_in = None
            self.__logged_in_at = datetime.now(timezone("Europe/Rome"))
            self.__endpoints = Endpoints(self)
            if not self.__me:
                self.__me = Me(self)

            await self.__me._fill_data(mobile_token)  # pylint: disable=protected-access

            return True
        except Exception as e:
            if handle_exc:
                return False

            raise e

    @property
    def token(self) -> Optional[str]:
        return self.__token

    @property
    def refresh_token(self) -> Optional[str]:
        return self.__refresh_token

    @property
    def expires_at(self) -> Optional[datetime]:
        if self.__login_response:
            if self.__expires_in is None:
                self.__expires_in = self.__login_response.get("expires_in")

            if self.__expires_in is not None and self.__logged_in_at is not None:
                return self.__logged_in_at + timedelta(seconds=self.__expires_in)

        return None

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

        try:
            self.me
        except ValueError:
            await self.login()
        else:
            if (
                self.me is None
                or self.token is None
                or self.expires_at is None
                or datetime.now(timezone("Europe/Rome")) >= self.expires_at
            ):
                await self.login()

        if not endpoint.startswith(self.BASE_URL):
            if urlsplit(endpoint).scheme:
                raise ValueError(
                    f"Invalid URL given: The URL provided is not for {self.BASE_URL}."
                )
            endpoint = urljoin(self.BASE_URL, endpoint.lstrip("/"))

        return await self._request(
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
            raise_for_status=raise_for_status,
            read_until_eof=read_until_eof,
            proxy=proxy,
            timeout=timeout,
            verify_ssl=verify_ssl,
            fingerprint=fingerprint,
            ssl_context=ssl_context,
            ssl=ssl,
            proxy_headers=proxy_headers,
            trace_request_ctx=trace_request_ctx,
            read_bufsize=read_bufsize,
        )

    async def _request(
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

        headers = headers or {}
        headers["Argo-Client-Version"] = self.app_version  # type: ignore
        headers["Authorization"] = f"Bearer {self.token}"  # type: ignore
        headers["X-Auth-Token"] = self.me.token  # type: ignore
        headers["X-Cod-Min"] = self.school_code  # type: ignore
        headers["X-Date-Exp-Auth"] = "9999-12-31 23-59-59.000"  # type: ignore

        async with self.session.request(
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
                if content.get("success", True) is False:
                    raise ResponseError(
                        status_code=response.status,
                        message=content.get(
                            "msg",
                            content.get("message", "Error in response from server"),
                        ),
                    )
            except aiohttp.ContentTypeError:
                content = (await response.content.read()).decode()

            return (content, response)
