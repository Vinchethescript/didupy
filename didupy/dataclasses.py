from dataclasses import dataclass
from typing import Tuple
from datetime import date
from typing import Union, Optional


@dataclass(frozen=True)
class SchoolData:
    name: str
    year: Tuple[date, date]
    class_: Union[int, str]
    section: str
    course: str


@dataclass(frozen=True)
class UserResidenceData:
    address: str
    postal_code: str
    city: str


@dataclass(frozen=True)
class UserData:
    last_class: bool
    full_name: str
    first_name: str
    last_name: str
    above_18: bool
    email: str
    cell: Optional[str]
    fiscal_code: str
    gender: str
    birth_date: date
    birth_place: str
    citizenship: str
    residence: UserResidenceData


@dataclass(frozen=True)
class ProfileOptions:
    orario_scolastico: bool
    pagellino_online: bool
    abilita_preautorizzazioni_fam: bool
    valutazioni_periodiche: bool
    abilita_pcto: bool
    visualizza_nota_valutazione: bool
    valutazioni_giornaliere: bool
    compiti_assegnati: bool
    ignora_opzione_voti_docenti: bool
    docenti_classe: bool
    recupero_debito_sf: bool
    rendi_visibile_curriculum: bool
    richiesta_certificati: bool
    modifica_recapiti: bool
    abilita_giustific_maggiorenni: bool
    consiglio_di_istituto: bool
    note_disciplinari: bool
    abilita_mensa: bool
    giudizi: bool
    abilita_pfi: bool
    mostra_media_materia: bool
    giustificazioni_assenze: bool
    tabellone_periodi_intermedi: bool
    pagelle_online: bool
    assenze_per_data: bool
    valutazioni_sospese_periodiche: bool
    argomenti_lezione: bool
    nascondi_didup_famiglia: bool
    alilita_bsmart_famiglia: bool
    voti_giudizi: bool
    recupero_debito_int: bool
    abilita_autocertificazione_fam: bool
    mostra_media_generale: bool
    tabellone_scrutinio_finale: bool
    pin_voti: bool
    disabilita_accesso_famiglia: bool
    tasse_scolastiche: bool
    promemoria_classe: bool
    prenotazione_alunni: bool
    consiglio_di_classe: bool


@dataclass(frozen=True)
class DashboardOptions(ProfileOptions):
    invalsi: bool
    pfi: bool
    asl: bool
    wsm: bool


@dataclass(frozen=True)
class Subject:
    shortcut: str
    scrutinizable: bool
    code: str
    counts_towards_avg: bool
    name: str
    pk: str

    def __repr__(self) -> str:
        return f"Subject(code={self.code!r}, shortcut={self.shortcut!r})"


@dataclass(frozen=True)
class Period:
    pk: str
    start_date: date
    name: str
    one_grade: bool
    avg: float
    is_avg: bool
    end_date: date
    code: str
    is_final: bool
