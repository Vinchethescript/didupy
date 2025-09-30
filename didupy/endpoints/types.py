from typing import Any, TypedDict, Literal


ArgoRequestHeaders = TypedDict(
    "ArgoRequestHeaders",
    {
        "Argo-Client-Version": str,
        "Authorization": str,
        "X-Auth-Token": str,
        "X-Cod-Min": str,
        "X-Date-Exp-Auth": str,
    },
)


class ArgoResponse(TypedDict):
    success: bool
    msg: None | str
    data: Any


# ======== Profilo ========


class AnnoProfilo(TypedDict):
    dataInizio: str
    anno: str
    dataFine: str


class AlunnoProfilo(TypedDict):
    isUltimaClasse: bool
    nominativo: str
    cognome: str
    nome: str
    pk: str
    maggiorenne: bool
    desEmail: str


class ClasseProfilo(TypedDict):
    pk: str
    desDenominazione: str
    desSezione: str


class CorsoProfilo(TypedDict):
    descrizione: str
    pk: str


class ScuolaProfilo(CorsoProfilo):
    desOrdine: str


class SchedaProfilo(TypedDict):
    classe: ClasseProfilo
    corso: CorsoProfilo
    sede: CorsoProfilo
    scuola: ScuolaProfilo
    pk: str


class ProfiloResponseData(TypedDict):
    resetPassword: bool
    ultimoCambioPwd: str
    anno: AnnoProfilo
    genitore: str
    profiloDisabilitato: bool
    isSpid: bool
    alunno: AlunnoProfilo
    scheda: SchedaProfilo
    primoAccesso: bool
    profiloStorico: bool


class ProfiloResponse(ArgoResponse):
    data: ProfiloResponseData


# ======= Dettaglio profilo =======


class DettaglioUtente(TypedDict):
    flgUtente: str


class DettaglioAlunno(TypedDict):
    cognome: str
    desCellulare: str | None
    desCf: str
    datNascita: str
    desCap: str
    desComuneResidenza: str
    nome: str
    desComuneNascita: str
    desCapResidenza: str
    cittadinanza: str
    desIndirizzoRecapito: str
    desEMail: str
    nominativo: str
    desVia: str
    desTelefono: str | None
    sesso: str
    desComuneRecapito: str


class DettaglioProfiloResponseData(ArgoResponse):
    utente: DettaglioUtente
    genitore: dict
    alunno: DettaglioAlunno


class DettaglioProfiloResponse(ArgoResponse):
    data: DettaglioProfiloResponseData


# ======== Dashboard ========


class DashboardRequest(TypedDict):
    dataultimoaggiornamento: str


class Opzione(TypedDict):
    valore: bool
    chiave: str


class Materia(TypedDict):
    abbreviazione: str
    scrut: bool
    codTipo: str
    faMedia: bool
    materia: str
    pk: str


class Periodo(TypedDict):
    pkPeriodo: str
    dataInizio: str
    descrizione: str
    votoUnico: bool
    mediaScrutinio: float
    isMediaScrutinio: bool
    dataFine: str
    codPeriodo: str
    isScrutinioFinale: bool


class BachecaAllegato(TypedDict):
    nomeFile: str
    path: str
    descrizioneFile: str
    pk: str
    url: str


class BachecaEntry(TypedDict):
    datEvento: str
    messaggio: str
    data: str
    pvRichiesta: bool
    categoria: str
    dataConfermaPresaVisione: str
    url: None | str
    autore: str
    dataScadenza: str
    operazione: str
    adRichiesta: bool
    isPresaVisione: bool
    dataConfermaAdesione: str
    pk: str
    listaAllegati: list[BachecaAllegato]
    dataScadAdesione: None | str
    isPresaAdesioneConfermata: bool


class FileCondivisi(TypedDict):
    fileAlunniScollegati: list
    listaFile: list


class DocenteClasse(TypedDict):
    desCognome: str
    materie: list[str]
    desNome: str
    pk: str
    desEmail: str


class Autocert(TypedDict):
    datUpdate: None
    flgComunicato: None


class Frase(TypedDict):
    frase: str


class Autocertificazione(TypedDict):
    autocert: Autocert
    listaFrasi: list[Frase]


class Compito(TypedDict):
    compito: str
    dataConsegna: str


class RegistroEntry(TypedDict):
    datEvento: str
    isFirmato: bool
    compiti: list[Compito]
    docente: str
    pkMateria: str
    operazione: str
    desUrl: None | str
    pkDocente: str
    datGiorno: str
    materia: str
    pk: str
    attivita: str
    ora: int


class AppelloEntry(TypedDict):
    operazione: str
    datEvento: str
    descrizione: str
    daGiustificare: bool
    giustificata: str
    data: str
    codEvento: str
    docente: str
    commentoGiustificazione: str
    pk: str
    dataGiustificazione: str
    nota: str


class DashboardResponseDatum(TypedDict):
    fuoriClasse: list
    msg: str
    opzioni: list[Opzione]
    mediaGenerale: float
    mediaPerMese: dict[str, float]
    listaMaterie: list[Materia]
    rimuoviDatiLocali: bool
    listaPeriodi: list[Periodo]
    promemoria: list  # TODO: define
    bacheca: list[BachecaEntry]
    fileCondivisi: FileCondivisi
    voti: list  # TODO: define
    ricaricaDati: bool
    listaDocentiClasse: list[DocenteClasse]
    autocertificazione: Autocertificazione
    registro: list[RegistroEntry]
    schede: list  # TODO: define
    prenotazioniAlunni: list
    noteDisciplinari: list
    pk: str
    classiExtra: bool


class DashboardResponseData(TypedDict):
    dati: list[DashboardResponseDatum]


class DashboardResponse(ArgoResponse):
    data: DashboardResponseData


# ======== Orario giorno ========


class OrarioGiornoEntry(TypedDict):
    numOra: int
    mostra: bool
    desCognome: str
    desNome: str
    docente: str
    materia: str
    pk: str
    scuAnagrafePK: str
    desDenominazione: str
    desEmail: str
    desSezione: str
    ora: None | str


class OrarioGiornoResponseData(TypedDict):
    dati: dict[
        Literal["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
        list[OrarioGiornoEntry],
    ]


class OrarioGiornoResponse(ArgoResponse):
    data: OrarioGiornoResponseData


# ======== Curriculum ========


class CurriculumEntry(TypedDict):
    pkScheda: str
    classe: str
    anno: int
    esito: str
    mostraCredito: bool
    isSuperiore: bool
    credito: int
    isInterruzioneFR: bool
    media: float | None
    CVAbilitato: bool
    ordineScuola: str
    mostraInfo: bool


class CurriculumResponseData(TypedDict):
    curriculum: list[CurriculumEntry]


class CurriculumResponse(ArgoResponse):
    data: CurriculumResponseData


# ======== Other Endpoints ========
class DownloadBachecaResponse(ArgoResponse):
    url: str


class PresaVisioneAdesioneResponse(ArgoResponse):
    pass


del DownloadBachecaResponse.__annotations__["data"]
del PresaVisioneAdesioneResponse.__annotations__["data"]
