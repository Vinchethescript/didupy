from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Any
from datetime import date as Date, time
from typing import Union, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .dashboard import Dashboard


class AbsenceType(Enum):
    absence = "A"
    exit = "U"
    # TODO: find out other event codes
    # THIS MIGHT BREAK UNTIL COMPLETED


def _make_repr(self, **kwargs) -> str:
    args = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"{type(self).__name__}({args})"


@dataclass(frozen=True)
class CommonObject:
    pk: str


@dataclass(frozen=True)
class SubjectGrades:
    num: int
    sum: float
    avg: float


@dataclass(frozen=True)
class SubjectAverages:
    oral: SubjectGrades
    written: SubjectGrades
    total: SubjectGrades
    grades: int

    def __int__(self) -> int:
        return self.grades

    def __float__(self) -> float:
        return self.total.avg

    def __repr__(self) -> str:
        return _make_repr(
            self,
            grades=self.grades,
            oral=self.oral.avg,
            written=self.written.avg,
            total=self.total.avg,
        )


@dataclass(frozen=True)
class SchoolData(CommonObject):
    name: str
    year: Tuple[Date, Date]
    class_: Union[int, str]
    section: str
    course: str


@dataclass(frozen=True)
class UserResidenceData:
    address: str
    postal_code: str
    city: str


@dataclass(frozen=True)
class UserData(CommonObject):
    last_class: bool
    full_name: str
    first_name: str
    last_name: str
    above_18: bool
    email: str
    cell: Optional[str]
    fiscal_code: str
    gender: str
    birth_date: Date
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
class PartialTeacher(CommonObject):
    name: str

@dataclass(frozen=True)
class Teacher(CommonObject):
    first_name: str
    last_name: str
    email: str
    subjects: Sequence[Union["SubjectType", str]]  # str for missing subject data

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"

    def __repr__(self) -> str:
        return _make_repr(
            self,
            full_name=self.full_name,
            subjects=self.subjects,
        )

    def __str__(self) -> str:
        return self.full_name


@dataclass(frozen=True)
class PartialSubject(CommonObject):
    shortcut: str
    scrutinizable: bool
    type: str
    counts_towards_avg: bool
    name: str
    dashboard: "Dashboard"
    averages: SubjectAverages

    def __repr__(self) -> str:
        return _make_repr(
            self,
            shortcut=self.shortcut,
            type=self.type,
        )

    def __str__(self) -> str:
        return self.name

    @property
    def grades(self) -> Sequence["Grade"]:
        full = self.dashboard.grades

        return list(
            filter(
                lambda g: isinstance(g.subject, PartialSubject)
                and g.subject.pk == self.pk,
                full,
            )
        )

    @property
    def teachers(self) -> Sequence[Teacher]:
        full = self.dashboard.teachers
        ret = []
        for teacher in full:
            for subject in teacher.subjects:
                if isinstance(subject, PartialSubject) and subject.pk == self.pk:
                    ret.append(teacher)
                    break

        return ret


@dataclass(frozen=True)
class Subject(PartialSubject):
    code: str
    ministerial_code: str
    description: Optional[str]
    has_failing_grades: bool
    has_individual_lessons: bool
    full_name: str
    kind: str
    id: str

    def __repr__(self) -> str:
        return _make_repr(
            self,
            shortcut=self.shortcut,
            type=self.type,
            code=self.code,
        )

    def __str__(self) -> str:
        return self.full_name


@dataclass(frozen=True)
class Period(CommonObject):
    start_date: Date
    name: str
    one_grade: bool
    avg: float
    is_avg: bool
    end_date: Date
    code: str
    is_final: bool
    dashboard: "Dashboard"

    @property
    def start(self) -> Date:
        """Alias for start_date"""
        return self.start_date

    @property
    def end(self) -> Date:
        """Alias for end_date"""
        return self.end_date

    def __repr__(self) -> str:
        return _make_repr(
            self,
            name=self.name,
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def __str__(self) -> str:
        return self.name

    @property
    def grades(self) -> Sequence["Grade"]:
        full = self.dashboard.grades

        return [grade for grade in full if grade.period.pk == self.pk]

    @property
    def register(self) -> Sequence["Day"]:
        full = self.dashboard.register

        return [day for day in full if day.period.pk == self.pk]


@dataclass(frozen=True)
class Grade(CommonObject):
    created_at: Date
    """When the grade was added to the system"""

    period: Period
    label: str
    big_label: str
    value: Union[float, int]
    # find out what codVotoPratico means
    # ignore docente as we get its pk later
    subject: PartialSubject
    # find out what tipoValutazione means
    # find out what prgVoto means
    # find out what operazione means
    description: str
    # find out what faMenoMedia means
    teacher: Teacher  # implement
    comment: str

    date: Date
    """Date of the grade (might be different from created_at)"""

    counts_towards_avg: bool

    def __repr__(self) -> str:
        return _make_repr(
            self,
            subject=self.subject,
            label=self.label,
            value=self.value,
            date=self.date,
        )

    def __str__(self) -> str:
        return f"{self.subject.shortcut}: {self.label}"


@dataclass(frozen=True)
class Reminder(CommonObject):
    date: Date
    start_time: time
    end_time: time
    teacher: Teacher
    note: str

    def __str__(self) -> str:
        return f"{self.teacher.full_name}: {self.note} [{self.date} {self.start_time}-{self.end_time}]"

    @property
    def start(self):
        """Alias for start_time"""
        return self.start_time

    @property
    def end(self):
        """Alias for end_time"""
        return self.end_time


@dataclass(frozen=True)
class Justification:
    date: Date
    comment: str

    def __str__(self) -> str:
        return self.comment


@dataclass(frozen=True)
class AbsenceEvent(CommonObject):
    date: Date
    type: AbsenceType
    justifiable: bool
    teacher_name: str
    note: str
    description: str
    justification: Optional[Justification]

    def __repr__(self) -> str:
        return _make_repr(
            self,
            type=self.type,
            date=self.date,
            teacher=self.teacher_name,
            justification=self.justification,
        )

@dataclass(frozen=True)
class OutOfClass(CommonObject):
    date: Date
    note: str
    teacher_name: str
    description: str
    online: bool

@dataclass(frozen=True)
class HomeworkAssigned:
    text: str
    date: Date
    due_date: Date
    teacher: Teacher
    subject: Union[SubjectType, str]

    def __repr__(self) -> str:
        return _make_repr(
            self,
            subject=self.subject,
            date=self.date,
            due_date=self.due_date,
        )

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class DayEvent(CommonObject):
    date: Date
    teacher: Teacher
    subject: Union[SubjectType, str]
    url: Optional[str]
    activity: str
    signed: bool
    hour: int
    homework: Sequence[HomeworkAssigned]

    def __repr__(self) -> str:
        return _make_repr(
            self,
            signed=self.signed,
            subject=self.subject,
            date=self.date,
            hour=self.hour,
            activity=self.activity,
        )


@dataclass(frozen=True)
class Day:
    date: Date
    period: Period
    absence: Optional[AbsenceEvent]
    grades: Sequence[Grade]
    reminders: Sequence[Reminder]
    events: Sequence[DayEvent]
    homework: Sequence[HomeworkAssigned]

    def __repr__(self) -> str:
        return _make_repr(
            self,
            date=self.date,
            absence=self.absence,
            events=self.events,
            homework=self.homework,
        )
    
@dataclass(frozen=True)
class SharedFile(CommonObject):
    file: Any # just give this directly for now
    date: Date
    message: str
    folder: str
    teacher: Teacher
    attachments: list # to implement
    url: str


SubjectType = Union[Subject, PartialSubject]
