import os, datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.hash import bcrypt
from sqlmodel import (
    SQLModel, Field, Relationship, Session, create_engine,
    select, delete
)
from dotenv import load_dotenv

# ─────────────────────────────── Models ─────────────────────────────── #
class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    persons: List["Person"] = Relationship(back_populates="group")
    events:  List["Event"]  = Relationship(back_populates="group")

class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    warning:   bool = False
    suspended: bool = False
    group_id:  int  = Field(foreign_key="group.id")
    group:     Group = Relationship(back_populates="persons")
    attendance: List["Attendance"] = Relationship(back_populates="person")

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    starts_at: datetime.datetime
    group_id: int = Field(foreign_key="group.id")
    group:    Group = Relationship(back_populates="events")
    attendance: List["Attendance"] = Relationship(back_populates="event")

class Attendance(SQLModel, table=True):
    person_id: int = Field(foreign_key="person.id", primary_key=True)
    event_id:  int = Field(foreign_key="event.id",  primary_key=True)
    status: str = "ABSENT"                     # PRESENT | ABSENT
    person: Person = Relationship(back_populates="attendance")
    event:  Event  = Relationship(back_populates="attendance")

# ─────────────────────────────── Auth ───────────────────────────────── #
load_dotenv()
ALGORITHM = "HS256"
SECRET    = os.getenv("JWT_SECRET")
security  = HTTPBearer()

def create_token() -> str:
    payload = {"sub": "admin",
               "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def admin_login(email: str, password: str) -> str:
    if email == os.getenv("ADMIN_EMAIL") and bcrypt.verify(password, os.getenv("ADMIN_PWD_HASH")):
        return create_token()
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")

def admin_only(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token invalid")

# ─────────────────────────────── DB / App ───────────────────────────── #
engine = create_engine(os.getenv("DATABASE_URL"), echo=False)
SQLModel.metadata.create_all(engine)

app = FastAPI(title="SSTM Attendance API", version="0.2.1")

def get_session():
    with Session(engine) as session:
        yield session

# ─────────────────────────────── Routes ─────────────────────────────── #
## AUTH
@app.post("/login")
def login(email: str, password: str):
    return {"access_token": admin_login(email, password)}

## PUBLIC READ
@app.get("/groups")
def list_groups(session: Session = Depends(get_session)):
    return session.exec(select(Group)).all()

from typing import List, Dict
from sqlmodel import select

# ...

@app.get("/groups/{gid}/summary")
def summary(gid: int, session: Session = Depends(get_session)) -> List[Dict]:
    """
    Retorna um resumo (presenças/faltas) do grupo `gid`.

    Saída:
        [
            {"person_id": 1, "status": "PRESENT"},
            {"person_id": 2, "status": "ABSENT"},
            ...
        ]
    """
    rows = session.exec(
        select(Attendance.person_id, Attendance.status)
        .join(Event)
        .where(Event.group_id == gid)
    ).all()

    # Converte cada tupla em dicionário JSON-friendly
    return [{"person_id": pid, "status": st} for pid, st in rows]


## ADMIN CREATE
@app.post("/groups", dependencies=[Depends(admin_only)])
def create_group(group: Group, session: Session = Depends(get_session)):
    session.add(group); session.commit(); session.refresh(group)
    return group

@app.post("/groups/{gid}/persons", dependencies=[Depends(admin_only)])
def add_person(gid: int, person: Person, session: Session = Depends(get_session)):
    person.group_id = gid
    session.add(person); session.commit(); session.refresh(person)
    return person

@app.post("/groups/{gid}/events", dependencies=[Depends(admin_only)])
def add_event(gid: int, event: Event, session: Session = Depends(get_session)):
    # converte string ISO → datetime, se necessário
    if isinstance(event.starts_at, str):
        event.starts_at = datetime.datetime.fromisoformat(
            event.starts_at.replace("Z", "+00:00").replace(" ", "T")
        )
    event.group_id = gid
    session.add(event); session.commit(); session.refresh(event)
    return event

## ADMIN DELETE
@app.delete("/groups/{gid}", status_code=204, dependencies=[Depends(admin_only)])
def delete_group(gid: int, session: Session = Depends(get_session)):
    events_ids = [e.id for e in session.exec(select(Event.id).where(Event.group_id == gid))]
    if events_ids:
        session.exec(delete(Attendance).where(Attendance.event_id.in_(events_ids)))
        session.exec(delete(Event).where(Event.id.in_(events_ids)))
    session.exec(delete(Person).where(Person.group_id == gid))
    deleted = session.exec(delete(Group).where(Group.id == gid))
    session.commit()
    if deleted.rowcount == 0:
        raise HTTPException(404, "Group not found")

@app.delete("/persons/{pid}", status_code=204, dependencies=[Depends(admin_only)])
def delete_person(pid: int, session: Session = Depends(get_session)):
    session.exec(delete(Attendance).where(Attendance.person_id == pid))
    deleted = session.exec(delete(Person).where(Person.id == pid))
    session.commit()
    if deleted.rowcount == 0:
        raise HTTPException(404, "Person not found")

@app.delete("/events/{eid}", status_code=204, dependencies=[Depends(admin_only)])
def delete_event(eid: int, session: Session = Depends(get_session)):
    session.exec(delete(Attendance).where(Attendance.event_id == eid))
    deleted = session.exec(delete(Event).where(Event.id == eid))
    session.commit()
    if deleted.rowcount == 0:
        raise HTTPException(404, "Event not found")

## ATTENDANCE
@app.post("/events/{eid}/attendance", dependencies=[Depends(admin_only)])
def mark_attendance(
    eid: int, person_id: int, status: str,
    session: Session = Depends(get_session)
):
    if status not in {"PRESENT", "ABSENT"}:
        raise HTTPException(400, "status must be PRESENT|ABSENT")

    att = session.get(Attendance, (person_id, eid))
    if att:
        att.status = status
    else:
        session.add(Attendance(person_id=person_id, event_id=eid, status=status))
    session.commit()

    absences = len(
        session.exec(
            select(Attendance).where(
                Attendance.person_id == person_id,
                Attendance.status == "ABSENT"
            )
        ).all()
    )
    person = session.get(Person, person_id)
    person.warning   = 3 <= absences < 5
    person.suspended = absences >= 5
    session.add(person); session.commit()

    return {"absences": absences, "warning": person.warning, "suspended": person.suspended}
