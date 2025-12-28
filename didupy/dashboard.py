import io
from datetime import date, time
from typing import Union, BinaryIO, Optional
from .dataclasses import (
    DashboardOptions,
    Period,
    Grade,
    PartialSubject,
    Subject,
    Teacher,
    SubjectAverages,
    SubjectGrades,
    SubjectType,
    Reminder,
    AbsenceEvent,
    AbsenceType,
    Justification,
    DayEvent,
    HomeworkAssigned,
    Day,
    PartialTeacher
)
from .endpoints.types import (
    BachecaEntry,
    BachecaAllegato,
    DashboardResponseDatum,
    Materia,
)


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

        self.__homework = None

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
        self.__teachers = None
        self.__grades = None
        self.__options = None
        self.__other_options = None
        self.__periods = None
        self.__inbox = None
        self.__reminders = None
        self.__absences = None
        self.__homework = None
        self.__register = None

    def _get_subject(self, pk: str, data: Optional[DashboardResponseDatum] = None):
        if data is None or self.__subjects is None:
            if self.__data is None or self.__subjects is None:
                raise ValueError("Dashboard data not filled. Log in first.")

            data = self.__data

        subj = list(filter(lambda x: x.pk == pk, self.subjects))
        if subj:
            return subj[0]
        else:
            part_subj = list(filter(lambda x: x["pk"] == pk, data["listaMaterie"]))
            if not part_subj:
                return

            part_subj = part_subj[0]

            _avgs = data["mediaMaterie"].get(pk, {})
            avgs = SubjectAverages(
                oral=SubjectGrades(
                    sum=_avgs.get("sommaValutazioniOrale", 0.0),
                    num=_avgs.get("numValutazioniOrale", 0),
                    avg=_avgs.get("mediaOrale", 0.0),
                ),
                written=SubjectGrades(
                    sum=_avgs.get("sommaValutazioniScritto", 0.0),
                    num=_avgs.get("numValutazioniScritto", 0),
                    avg=_avgs.get("mediaScritta", 0.0),
                ),
                total=SubjectGrades(
                    sum=_avgs.get("sumValori", 0.0),
                    num=_avgs.get("numValori", 0),
                    avg=_avgs.get("mediaMateria", 0.0),
                ),
                grades=_avgs.get("numVoti", 0),
            )

            def _(ps: Materia):
                return PartialSubject(
                    dashboard=self,
                    shortcut=ps["abbreviazione"],
                    scrutinizable=ps["scrut"],
                    type=ps["codTipo"],
                    counts_towards_avg=ps["faMedia"],
                    name=ps["materia"],
                    pk=ps["pk"],
                    averages=avgs,
                )

            # try finding it from the grades
            sub = list(
                filter(lambda x: x["pkMateria"] == part_subj["pk"], data["voti"])
            )
            if sub:
                sub = sub[0].get("materiaLight", None)
                if sub:
                    subj = Subject(
                        dashboard=self,
                        shortcut=part_subj["abbreviazione"],
                        scrutinizable=part_subj["scrut"],
                        type=part_subj["codTipo"],
                        counts_towards_avg=part_subj["faMedia"],
                        name=part_subj["materia"],
                        pk=part_subj["pk"],
                        code=sub["codMateria"],
                        ministerial_code=sub["codMinisteriale"],
                        description=sub.get("descrizione", None),
                        has_failing_grades=sub["conInsufficienze"],
                        has_individual_lessons=sub["lezioniIndividuali"],
                        full_name=sub["codEDescrizioneMateria"],
                        kind=sub["tipo"],
                        id=sub["idmateria"],
                        averages=avgs,
                    )
                else:
                    subj = _(part_subj)
            else:
                subj = _(part_subj)

            self.__subjects.append(subj)
            return subj

    def _get_subject_from_shortcut(
        self, shortcut: str, data: Optional[DashboardResponseDatum] = None
    ):
        # probably not the best way to do this, but oh well this is what argo gives me
        if data is None:
            if self.__data is None:
                raise ValueError("Dashboard data not filled. Log in first.")

            data = self.__data

        subj = list(filter(lambda x: x.shortcut == shortcut, self.subjects))
        if subj:
            return subj[0]
        else:
            part_subj = list(
                filter(lambda x: x["abbreviazione"] == shortcut, data["listaMaterie"])
            )
            if not part_subj:
                return

            part_subj = part_subj[0]
            return self._get_subject(part_subj["pk"], data)

    def _get_teacher(
        self, pk: str, data: Optional[DashboardResponseDatum] = None
    ) -> Teacher:
        if data is None or self.__teachers is None:
            if self.__data is None or self.__teachers is None:
                raise ValueError("Dashboard data not filled. Log in first.")

            data = self.__data

        teacher = list(filter(lambda x: x.pk == pk, self.teachers))
        if teacher:
            return teacher[0]

        teacher = list(filter(lambda x: x["pk"] == pk, data["listaDocentiClasse"]))
        if not teacher:
            return PartialTeacher(
                pk=pk,
                name="Unknown"
            ) # to be typed properly
            #raise ValueError(f"Teacher with pk {pk} not found")

        teacher = teacher[0]
        subjects = []
        for shortcut in teacher["materie"]:
            subj = self._get_subject_from_shortcut(shortcut, data)
            if subj:
                subjects.append(subj)
            else:
                subjects.append(
                    shortcut
                )  # keep the shortcut if we can't find the subject

        ret = Teacher(
            pk=teacher["pk"],
            first_name=teacher["desNome"],
            last_name=teacher["desCognome"],
            email=teacher["desEmail"],
            subjects=subjects,
        )

        self.__teachers.append(ret)

        return ret

    async def fetch(self):
        data = (await self.client.endpoints.dashboard())["data"]["dati"]
        new = list(filter(lambda x: x["pk"] == self.client.me.user_pk, data))
        if new:
            self.__data = new[0]
        else:
            # not sure, but at least we have something
            # if this is correct, then we should use this
            # to implement multi-account support
            self.__data = data[0]

        data = self.__data  # for easier access

        self.__periods = [
            Period(
                dashboard=self,
                pk=period["pkPeriodo"],
                start_date=date.fromisoformat(period.get("datInizio") or period.get("dataInizio")),
                name=period["descrizione"],
                one_grade=period["votoUnico"],
                avg=period["mediaScrutinio"],
                is_avg=period["isMediaScrutinio"],
                end_date=date.fromisoformat(period.get("datFine") or period.get("dataFine")),
                code=period["codPeriodo"],
                is_final=period["isScrutinioFinale"],
            )
            for period in data["listaPeriodi"]
        ]

        self.__teachers = []
        self.__subjects = []
        self.__grades = []

        for grd in data["voti"]:
            subj = self._get_subject(grd["pkMateria"], data)
            if subj is None:
                # should not happen
                continue

            teacher = (
                self._get_teacher(grd["pkDocente"], data) if grd["pkDocente"] else None
            )
            if teacher is None:
                # don't think this is gonna happen
                continue

            period = list(filter(lambda x: x.pk == grd["pkPeriodo"], self.periods))
            if not period:
                # this ain't happening anyway (????????????)
                continue

            self.__grades.append(
                Grade(
                    pk=grd["pk"],
                    created_at=date.fromisoformat(grd["datEvento"]),
                    date=date.fromisoformat(grd["datGiorno"]),
                    period=period.pop(),
                    label=grd["codCodice"],
                    big_label=grd["descrizioneVoto"],
                    value=grd["valore"],
                    subject=subj,
                    description=grd["descrizioneProva"],
                    comment=grd["desCommento"],
                    teacher=teacher,
                    counts_towards_avg=bool(grd["numMedia"]),
                )
            )

        for subj in data["listaMaterie"]:
            pk = subj["pk"]
            if not any(s.pk == pk for s in self.subjects):
                self._get_subject(pk, data)

        for teacher in data["listaDocentiClasse"]:
            pk = teacher["pk"]
            if not any(t.pk == pk for t in self.teachers):
                self._get_teacher(pk, data)

        kwargs = {}
        opts = {}
        annotations = DashboardOptions.__annotations__
        for b in DashboardOptions.__bases__:
            annotations.update(b.__annotations__)

        for opt in data["opzioni"]:
            k = opt["chiave"].lower()
            v = opt["valore"]
            if k in annotations:
                kwargs[k] = v
            else:
                opts[k] = v

        self.__options = DashboardOptions(**kwargs)
        self.__other_options = opts

        self.__inbox = [InboxItem(self.client, entry) for entry in data["bacheca"]]

        self.__reminders = [
            Reminder(
                pk=rem["pk"],
                date=date.fromisoformat(rem["datGiorno"]),
                start_time=time.fromisoformat(rem["oraInizio"]),
                end_time=time.fromisoformat(rem["oraFine"]),
                teacher=self._get_teacher(rem["pkDocente"], data),
                note=rem["desAnnotazioni"],
            )
            for rem in data.get("promemoria", [])
        ]

        self.__absences = [
            AbsenceEvent(
                pk=absc["pk"],
                date=date.fromisoformat(absc["data"]),
                type=AbsenceType(absc["codEvento"]),
                justifiable=absc["daGiustificare"],
                teacher_name=absc["docente"] or "",
                note=absc["nota"] or "",
                description=absc["descrizione"] or "",
                justification=(
                    Justification(
                        date=date.fromisoformat(absc["dataGiustificazione"]),
                        comment=absc["commentoGiustificazione"],
                    )
                    if absc.get("giustificata", "N") == "S"
                    else None
                ),
            )
            for absc in data.get("appello", [])
        ]

        self.__homework = []

        events = {}
        for item in data["registro"]:
            _date = item["datGiorno"]
            teacher = self._get_teacher(item["pkDocente"], data)
            subject = self._get_subject(item["pkMateria"], data)
            date_ = date.fromisoformat(_date)
            hw = [
                HomeworkAssigned(
                    text=h["compito"],
                    date=date_,
                    due_date=date.fromisoformat(h["dataConsegna"]),
                    teacher=teacher,
                    subject=subject if subject else item["materia"],
                )
                for h in item.get("compiti", [])
            ]

            evt = DayEvent(
                pk=item["pk"],
                date=date_,
                teacher=teacher,
                subject=subject if subject else item["materia"],
                url=item.get("url", None),
                activity=item["attivita"],
                signed=item["isFirmato"],
                hour=item["ora"],
                homework=hw,
            )

            self.__homework.extend(hw)
            if _date not in events:
                events[_date] = []

            events[_date].append(evt)

        self.__register = []
        dates = set(events.keys())
        for g in self.grades:
            dates.add(g.date.isoformat())

        for r in self.reminders:
            dates.add(r.date.isoformat())

        for _date in dates:
            date_ = date.fromisoformat(_date)
            period = list(
                filter(lambda x: x.start_date <= date_ <= x.end_date, self.periods)
            )
            if not period:
                continue

            period = period[0]
            absence = list(filter(lambda x: x.date == date_, self.absences))
            absence = absence[0] if absence else None

            self.__register.append(
                Day(
                    date=date_,
                    period=period,
                    absence=absence,
                    grades=[g for g in self.grades if g.date == date_],
                    reminders=[r for r in self.reminders if r.date == date_],
                    events=events.get(_date, []),
                    homework=[hw for hw in self.homework if hw.due_date == date_],
                )
            )

        self.__register.sort(key=lambda x: x.date)

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
    def subjects(self) -> list[SubjectType]:
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
    def reminders(self) -> list[Reminder]:
        if self.__reminders is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__reminders

    @property
    def shared_files(self) -> list:
        # fileCondivisi
        raise NotImplementedError

    @property
    def grades(self) -> list[Grade]:
        if self.__grades is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__grades

    @property
    def teachers(self) -> list[Teacher]:
        if self.__teachers is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__teachers

    @property
    def absences(self) -> list[AbsenceEvent]:
        if self.__absences is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__absences

    @property
    def homework(self) -> list[HomeworkAssigned]:
        if self.__homework is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__homework

    @property
    def assigned_homework(self) -> list[HomeworkAssigned]:
        today = date.today()
        return [hw for hw in self.homework if hw.due_date >= today]

    @property
    def past_homework(self) -> list[HomeworkAssigned]:
        today = date.today()
        return [hw for hw in self.homework if hw.due_date < today]

    @property
    def register(self) -> list[Day]:
        if self.__register is None:
            raise ValueError("Dashboard data not filled. Log in first.")

        return self.__register

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
