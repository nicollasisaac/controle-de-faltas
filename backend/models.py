from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import datetime     

class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    persons: List["Person"] = Relationship(back_populates="group")
    events: List["Event"]  = Relationship(back_populates="group")

class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    warning: bool = False
    suspended: bool = False
    group_id: int = Field(foreign_key="group.id")
    group: Group = Relationship(back_populates="persons")
    attendance: List["Attendance"] = Relationship(back_populates="person")

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    starts_at:datetime.datetime      
    group_id: int = Field(foreign_key="group.id")
    group: Group = Relationship(back_populates="events")
    attendance: List["Attendance"] = Relationship(back_populates="event")

class Attendance(SQLModel, table=True):
    person_id: int = Field(foreign_key="person.id", primary_key=True)
    event_id: int  = Field(foreign_key="event.id",  primary_key=True)
    status: str = "ABSENT"  # PRESENT | ABSENT
    person: Person = Relationship(back_populates="attendance")
    event:  Event  = Relationship(back_populates="attendance")
