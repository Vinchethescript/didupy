from typing import Dict
from datetime import date
from .dashboard import Dashboard
from .dataclasses import SchoolData, UserData, UserResidenceData, ProfileOptions


class Me:
    def __init__(self, client):
        from .client import DidUPClient

        self.client: DidUPClient = client
        self.__mobile_token: str = ""
        self.__options: Dict[str, bool] = {}
        self.__user = None
        self.__school = None
        self.__user_pk = ""
        self.__dashboard = None

    async def _fill_data(self, mobile_login: dict):
        try:
            data = list(
                filter(
                    lambda x: x.get("username", None) == self.client.username,
                    mobile_login.get("data", []),
                )
            ).pop(0)
        except IndexError:
            raise ValueError("No valid profile found.") from None

        self.__mobile_token = data["token"]
        self.__options = {a["chiave"]: a["valore"] for a in data.get("opzioni", [])}
        self.__dashboard = Dashboard(self.client)
        await self.__dashboard.fetch()
        await self.fetch()

    async def fetch(self):
        profile = await self.client.endpoints.profilo()
        profile_detail = await self.client.endpoints.dettaglio_profilo()
        data = profile["data"]
        scheda = data["scheda"]
        self.__user_pk = scheda["pk"]

        classe = scheda["classe"]
        try:
            classe_num = int(classe["desDenominazione"])
        except ValueError:
            classe_num = classe["desDenominazione"]

        self.__school = SchoolData(
            name=scheda["scuola"]["descrizione"],
            year=(
                date.fromisoformat(data["anno"]["dataInizio"]),
                date.fromisoformat(data["anno"]["dataFine"]),
            ),
            class_=classe_num,
            section=classe["desSezione"],
            course=scheda["corso"]["descrizione"],
            pk=scheda["scuola"]["pk"],
        )
        alunno = data["alunno"]
        alunno_det = profile_detail["data"]["alunno"]
        self.__user = UserData(
            pk=alunno["pk"],
            last_class=alunno["isUltimaClasse"],
            full_name=alunno["nominativo"],
            first_name=alunno["nome"],
            last_name=alunno["cognome"],
            above_18=alunno["maggiorenne"],
            email=alunno["desEmail"],
            cell=alunno_det["desCellulare"],
            fiscal_code=alunno_det["desCf"],
            gender=alunno_det["sesso"],
            birth_date=date.fromisoformat(alunno_det["datNascita"]),
            birth_place=alunno_det["desComuneNascita"],
            citizenship=alunno_det["cittadinanza"],
            residence=UserResidenceData(
                address=alunno_det["desIndirizzoRecapito"],
                postal_code=alunno_det["desCapResidenza"],
                city=alunno_det["desComuneResidenza"],
            ),
        )

        return self

    @property
    def dashboard(self) -> Dashboard:
        if self.__dashboard is None:
            raise ValueError("Dashboard not initialized. Log in first.")

        return self.__dashboard

    @property
    def user_pk(self) -> str:
        if self.__user_pk is None:
            raise ValueError("Profile data not filled. Log in first.")

        return self.__user_pk

    @property
    def token(self) -> str:
        if self.__mobile_token is None:
            raise ValueError("Profile data not filled. Log in first.")

        return self.__mobile_token

    @property
    def options(self) -> ProfileOptions:
        if self.__options is None:
            raise ValueError("Profile data not filled. Log in first.")

        kwargs = {}
        for k, v in self.__options.items():
            k = k.lower()
            if k in ProfileOptions.__annotations__:
                kwargs[k] = v

        return ProfileOptions(**kwargs)

    @property
    def other_options(self) -> Dict[str, bool]:
        if self.__options is None:
            raise ValueError("Profile data not filled. Log in first.")

        opts = {}
        for k, v in self.__options.items():
            k = k.lower()
            if k not in ProfileOptions.__annotations__:
                opts[k] = v
        return opts

    @property
    def school(self) -> SchoolData:
        if self.__school is None:
            raise ValueError("Profile data not filled. Log in first.")

        return self.__school

    @property
    def user(self) -> UserData:
        if self.__user is None:
            raise ValueError("Profile data not filled. Log in first.")

        return self.__user

    def __str__(self):
        return f"{self.user.full_name}"

    def __repr__(self):
        ret = [f"<{type(self).__name__}"]
        props = {
            "full_name": self.user.full_name,
            "school": self.school.name,
            "class": f"{self.school.class_}{self.school.section}",
            "course": self.school.course,
            "year": f"{self.school.year[0].year}-{self.school.year[1].year}",
        }
        for k, v in props.items():
            ret.append(f"{k}={v!r}")

        return " ".join(ret) + ">"
