import io
from datetime import date
from typing import Union, BinaryIO
from .dataclasses import DashboardOptions, Subject, Period
from .endpoints.types import BachecaEntry, BachecaAllegato


class ItemAttachment:
    def __init__(self, client, data: BachecaAllegato):
        from .client import DidUPClient

        self.__client: DidUPClient = client
        self.__data = data

    @property
    def pk(self) -> str:
        return self.__data["pk"]

    @property
    def filename(self) -> str:
        return self.__data["nomeFile"]

    @property
    def description(self) -> str:
        return self.__data["descrizioneFile"]

    @property
    def path(self) -> str:
        return self.__data["path"]

    @property
    def url(self) -> str:
        return self.__data["url"]

    async def get_download_url(self) -> str:
        resp = await self.__client.endpoints.download_allegato_bacheca(self.pk)
        return resp["url"]  # type: ignore

    async def download(self, fp: Union[BinaryIO, str]):
        should_close = False
        if isinstance(fp, str):
            fp = open(fp, "wb")
            should_close = True
        elif not isinstance(
            fp, (io.BytesIO, io.BufferedReader, io.RawIOBase, io.BufferedIOBase)
        ):
            raise TypeError("fp must be a file path or a binary file-like object")

        url = await self.get_download_url()

        # BROKEN: seems like this is always returning a 403 for some reason
        async with self.__client.session.get(url) as response:
            response.raise_for_status()

            data = await response.read()
            fp.write(data)
            if should_close:
                fp.close()

    def __repr__(self):
        ret = [f"<{type(self).__name__}"]
        props = {
            "filename": self.filename,
            "description": self.description,
            "path": self.path,
        }
        for k, v in props.items():
            ret.append(f"{k}={v!r}")

        return " ".join(ret) + ">"


class InboxItem:
    def __init__(self, client, data: BachecaEntry):
        from .client import DidUPClient

        self.__client: DidUPClient = client
        self.__data = data
        self.__date = date.fromisoformat(data["data"])
        self.__viewed_at = (
            date.fromisoformat(data["dataConfermaPresaVisione"])
            if data["dataConfermaPresaVisione"]
            else None
        )
        self.__expiration_date = (
            date.fromisoformat(data["dataScadenza"]) if data["dataScadenza"] else None
        )
        self.__attachments = [
            ItemAttachment(client, att) for att in data["listaAllegati"]
        ]

    @property
    def pk(self) -> str:
        return self.__data["pk"]

    @property
    def message(self) -> str:
        return self.__data["messaggio"]

    @property
    def expiration_date(self) -> date | None:
        return self.__expiration_date

    @property
    def viewed_at(self) -> date | None:
        return self.__viewed_at

    @property
    def date(self) -> date:
        return self.__date

    @property
    def category(self) -> str:
        return self.__data["categoria"]

    @property
    def author(self) -> str:
        return self.__data["autore"]

    @property
    def viewed(self) -> bool:
        return self.__data["isPresaVisione"]

    @property
    def confirmed(self) -> bool:
        return self.__data["isPresaAdesioneConfermata"]

    @property
    def attachments(self) -> list[ItemAttachment]:
        return self.__attachments

    async def mark_as_viewed(self):
        if not self.viewed:
            status = await self.__client.endpoints.presa_visione_adesione(self.pk, True)
            # we could re-fetch the whole dashboard, but this is probably enough
            self.__data["isPresaVisione"] = True
            return status

    def __repr__(self):
        ret = [f"<{type(self).__name__}"]
        props = {
            "viewed": self.viewed,
            "message": self.message,
            "author": self.author,
            "date": self.date,
            "attachments": len(self.attachments),
        }
        for k, v in props.items():
            ret.append(f"{k}={v!r}")

        return " ".join(ret) + ">"


class Dashboard:
    def __init__(self, client):
        from .client import DidUPClient

        self.client: DidUPClient = client
        self.__data = None
        self.__subjects = None
        self.__options = None
        self.__other_options = None
        self.__periods = None
        self.__inbox = None

    async def fetch(self):
        data = (await self.client.endpoints.dashboard())["data"]["dati"]
        new = list(filter(lambda x: x["pk"] == self.client.me.user_pk, data))
        if new:
            self.__data = new[0]
        else:
            self.__data = data[0]  # not sure, but at least we have something

        data = self.__data  # for easier access

        self.__subjects = [
            Subject(
                shortcut=subj["abbreviazione"],
                scrutinizable=subj["scrut"],
                code=subj["codTipo"],
                counts_towards_avg=subj["faMedia"],
                name=subj["materia"],
                pk=subj["pk"],
            )
            for subj in data["listaMaterie"]
        ]

        kwargs = {}
        opts = {}
        annotations = DashboardOptions.__annotations__
        for b in DashboardOptions.__bases__:
            annotations.update(b.__annotations__)

        for opt in self.__data["opzioni"]:
            k = opt["chiave"].lower()
            v = opt["valore"]
            if k in annotations:
                kwargs[k] = v
            else:
                opts[k] = v

        self.__options = DashboardOptions(**kwargs)
        self.__other_options = opts
        self.__periods = [
            Period(
                pk=period["pkPeriodo"],
                start_date=date.fromisoformat(period["dataInizio"]),
                name=period["descrizione"],
                one_grade=period["votoUnico"],
                avg=period["mediaScrutinio"],
                is_avg=period["isMediaScrutinio"],
                end_date=date.fromisoformat(period["dataFine"]),
                code=period["codPeriodo"],
                is_final=period["isScrutinioFinale"],
            )
            for period in data["listaPeriodi"]
        ]

        self.__inbox = [InboxItem(self.client, entry) for entry in data["bacheca"]]

        return self

    @property
    def options(self) -> DashboardOptions:
        if self.__options is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__options

    @property
    def other_options(self) -> dict[str, bool]:
        if self.__other_options is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__other_options

    @property
    def grades_general_avg(self) -> float:
        if self.__data is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__data["mediaGenerale"]

    @property
    def grades_monthly_avg(self) -> list[float]:
        if self.__data is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        avg = self.__data["mediaPerMese"]
        return list(avg.values())

    @property
    def subjects(self) -> list[Subject]:
        if self.__subjects is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__subjects

    @property
    def periods(self) -> list[Period]:
        if self.__periods is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__periods

    @property
    def inbox(self) -> list[InboxItem]:
        if self.__inbox is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__inbox

    @property
    def reminders(self) -> list:
        # promemoria
        raise NotImplementedError

    @property
    def shared_files(self) -> list:
        # fileCondivisi
        raise NotImplementedError

    @property
    def grades(self):
        # voti
        raise NotImplementedError

    @property
    def teachers(self):
        # listaDocentiClasse
        raise NotImplementedError

    @property
    def absences(self):
        # appello
        raise NotImplementedError

    def __repr__(self):
        ret = [f"<{type(self).__name__}"]
        props = {
            "subjects": len(self.subjects) if self.__subjects else None,
            "periods": len(self.periods) if self.__periods else None,
            "inbox_items": len(self.inbox) if self.__inbox else None,
            "grades_general_avg": self.grades_general_avg if self.__data else None,
        }
        for k, v in props.items():
            if v is not None:
                ret.append(f"{k}={v!r}")

        return " ".join(ret) + ">"
