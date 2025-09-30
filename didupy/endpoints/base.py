from datetime import datetime, date
from pytz import timezone
from .types import (
    ProfiloResponse,
    DashboardResponse,
    DownloadBachecaResponse,
    OrarioGiornoResponse,
    DettaglioProfiloResponse,
    CurriculumResponse,
    PresaVisioneAdesioneResponse,
)


class Endpoints:
    def __init__(self, client):
        from ..client import DidUPClient

        self.client: DidUPClient = client

    async def profilo(self) -> ProfiloResponse:
        content, _ = await self.client.request("GET", "profilo")
        return content  #  type: ignore

    async def dashboard(self) -> DashboardResponse:
        now = datetime.now(timezone("Europe/Rome"))
        content, _ = await self.client.request(
            "POST",
            "dashboard/dashboard",
            json={
                "dataultimoaggiornamento": now.strftime("%Y-%m-%d %H:%M:%S.%f"),
            },
        )
        return content  #  type: ignore

    async def presa_visione_adesione(
        self, pk: str, presa_visione: bool
    ) -> PresaVisioneAdesioneResponse:
        # TODO: find out what the response of this endpoint is
        content, _ = await self.client.request(
            "POST",
            "presavisioneadesione",
            json={
                "prgMessaggio": pk,
                "presaVisione": "S" if presa_visione else "N",
            },  # type: ignore
        )
        return content  #  type: ignore

    async def download_allegato_bacheca(self, pk: str) -> DownloadBachecaResponse:
        content, _ = await self.client.request(
            "POST", "downloadallegatobacheca", json={"uid": pk}
        )

        return content  #  type: ignore

    async def voti_scrutinio(self) -> dict:
        # to be typed
        content, _ = await self.client.request("POST", "votiscrutinio", json={})
        return content  # type: ignore

    async def orario_giorno(self, date_: date) -> OrarioGiornoResponse:
        content, _ = await self.client.request(
            "POST", "orario-giorno", json={"datGiorno": date_.strftime("%Y-%m-%d")}
        )

        return content  # type: ignore

    async def colloqui(self) -> dict:
        # to be typed
        content, _ = await self.client.request("POST", "ricevimento", json={})
        return content  # type: ignore

    async def pagamenti(self, pk_scheda: str) -> dict:
        # to be typed
        content, _ = await self.client.request(
            "POST", "pagamenti", json={"pkScheda": pk_scheda}
        )
        return content  # type: ignore

    async def curriculum(self) -> CurriculumResponse:

        # to be typed
        content, _ = await self.client.request("POST", "curriculumalunno", json={})
        return content  # type: ignore

    async def storico_bacheca(self, pk_scheda: str) -> dict:
        # TODO: find out what the response of this endpoint is
        content, _ = await self.client.request(
            "POST", "storicobacheca", json={"pkScheda": pk_scheda}
        )
        return content  # type: ignore

    async def storico_bacheca_alunno(self, pk_scheda: str) -> dict:
        # TODO: find out what the response of this endpoint is
        content, _ = await self.client.request(
            "POST", "storicobachecaalunno", json={"pkScheda": pk_scheda}
        )
        return content  # type: ignore

    async def dettaglio_profilo(self) -> DettaglioProfiloResponse:
        content, _ = await self.client.request("POST", "dettaglioprofilo", json={})
        return content  # type: ignore
