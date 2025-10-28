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


class ArgoResponseBase(TypedDict):
    success: bool
    msg: None | str


class ArgoResponse(ArgoResponseBase):
    data: Any


class CommonData(TypedDict):
    pk: str


# ======== Profilo ========


class AnnoProfilo(TypedDict):
    dataInizio: str
    anno: str
    dataFine: str


class AlunnoProfilo(CommonData):
    isUltimaClasse: bool
    nominativo: str
    cognome: str
    nome: str
    maggiorenne: bool
    desEmail: str


class ClasseProfilo(CommonData):
    desDenominazione: str
    desSezione: str


class CorsoProfilo(CommonData):
    descrizione: str


class ScuolaProfilo(CorsoProfilo):
    desOrdine: str


class SchedaProfilo(CommonData):
    classe: ClasseProfilo
    corso: CorsoProfilo
    sede: CorsoProfilo
    scuola: ScuolaProfilo


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


class Materia(CommonData):
    abbreviazione: str
    scrut: bool
    codTipo: str
    faMedia: bool
    materia: str


class MediaMateria(TypedDict):
    mediaMateria: float
    mediaOrale: float
    mediaScritta: float
    numValori: int
    numValutazioniOrale: int
    numValutazioniScritto: int
    numVoti: int
    sommaValutazioniOrale: float
    sommaValutazioniScritto: float
    sumValori: float


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


class BachecaAllegato(CommonData):
    nomeFile: str
    path: str
    descrizioneFile: str
    url: str


class BachecaEntry(CommonData):
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
    listaAllegati: list[BachecaAllegato]
    dataScadAdesione: None | str
    isPresaAdesioneConfermata: bool


class FileCondivisi(TypedDict):
    fileAlunniScollegati: list
    listaFile: list


class DocenteClasse(CommonData):
    desCognome: str
    materie: list[str]
    desNome: str
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


class RegistroEntry(CommonData):
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
    attivita: str
    ora: int


class AppelloEntry(CommonData):
    operazione: str
    datEvento: str
    descrizione: str
    daGiustificare: bool
    giustificata: str
    data: str
    codEvento: str
    docente: str
    commentoGiustificazione: str
    dataGiustificazione: str
    nota: str


class Promemoria(CommonData):
    operazione: str
    datEvento: str
    desAnnotazioni: str
    pkDocente: str
    flgVisibileFamiglia: str
    datGiorno: str
    docente: str
    oraInizio: str
    oraFine: str


class ScuMateriaPK(TypedDict):
    codMin: str
    prgScuola: int
    numAnno: int
    prgMateria: int


class MateriaLight(TypedDict):
    scumateriaPK: ScuMateriaPK
    codMateria: str
    desDescrizione: str
    desDescrAbbrev: str
    codSuddivisione: str
    codTipo: str
    flgConcorreMedia: str
    codAggrDisciplina: None | str
    flgLezioniIndividuali: None | str
    codAggrInvalsi: None | str
    codMinisteriale: str
    icona: str
    descrizione: None | str
    conInsufficienze: bool
    selezionata: bool
    tipoOnGrid: str
    prgMateria: int
    articolata: str
    tipo: str
    lezioniIndividuali: bool
    codEDescrizioneMateria: str
    idmateria: str


class Voto(CommonData):
    datEvento: str
    pkPeriodo: str
    codCodice: str
    valore: float
    codVotoPratico: str
    docente: str
    pkMateria: str
    tipoValutazione: None | str
    prgVoto: int
    operazione: str
    descrizioneProva: str
    faMenoMedia: str
    pkDocente: str
    descrizioneVoto: str
    codTipo: str
    datGiorno: str
    mese: int
    numMedia: float
    materiaLight: MateriaLight
    desMateria: str
    desCommento: str


class DashboardResponseDatum(CommonData):
    fuoriClasse: list
    msg: str
    opzioni: list[Opzione]
    mediaGenerale: float
    mediaPerMese: dict[str, float]
    mediaPerPeriodo: dict[str, float]
    mediaMaterie: dict[str, MediaMateria]
    listaMaterie: list[Materia]
    rimuoviDatiLocali: bool
    listaPeriodi: list[Periodo]
    promemoria: list[Promemoria]
    bacheca: list[BachecaEntry]
    bachecaAlunno: list[BachecaEntry]
    fileCondivisi: FileCondivisi
    voti: list[Voto]
    ricaricaDati: bool
    listaDocentiClasse: list[DocenteClasse]
    appello: list[AppelloEntry]
    profiloDisabilitato: bool
    autocertificazione: Autocertificazione
    registro: list[RegistroEntry]
    schede: list  # TODO: define
    prenotazioniAlunni: list
    noteDisciplinari: list
    classiExtra: bool


class DashboardResponseData(TypedDict):
    dati: list[DashboardResponseDatum]


class DashboardResponse(ArgoResponse):
    data: DashboardResponseData


# ======== Orario giorno ========


class OrarioGiornoEntry(CommonData):
    numOra: int
    mostra: bool
    desCognome: str
    desNome: str
    docente: str
    materia: str
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
class DownloadBachecaResponse(ArgoResponseBase):
    url: str


class PresaVisioneAdesioneResponse(ArgoResponseBase):
    pass
