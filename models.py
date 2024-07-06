from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import hashlib
import base64

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    uid = Column(String(10), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    teams = relationship("Team", secondary="team_members", back_populates="members")
    created_tasks = relationship("Task", back_populates="creator")
    assigned_tasks = relationship("Task", secondary="task_assignees", back_populates="assignees")
    tags = relationship("Tag", back_populates="user")

    @staticmethod
    def generate_uid(email, username):
        combined = email + username
        hash_object = hashlib.sha256(combined.encode())
        hex_dig = hash_object.hexdigest()
        b64_encoded = base64.b64encode(bytes.fromhex(hex_dig)).decode()
        return b64_encoded[:10]
    
    def __init__(self):
        self.uid = self.generate_uid(self.email, self.username)

class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("User", secondary="team_members", back_populates="teams")
    tasks = relationship("Task", back_populates="team")
    tags = relationship("Tag", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"

    team_id = Column(Integer, ForeignKey("teams.team_id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String)
    status = Column(String(20), nullable=False)
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    team_id = Column(Integer, ForeignKey("teams.team_id"))

    creator = relationship("User", back_populates="created_tasks")
    team = relationship("Team", back_populates="tasks")
    assignees = relationship("User", secondary="task_assignees", back_populates="assigned_tasks")
    tags = relationship("Tag", secondary="task_tags", back_populates="tasks")

class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    task_id = Column(Integer, ForeignKey("tasks.task_id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)

class Tag(Base):
    __tablename__ = "tags"

    tag_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    team_id = Column(Integer, ForeignKey("teams.team_id"))

    user = relationship("User", back_populates="tags")
    team = relationship("Team", back_populates="tags")
    tasks = relationship("Task", secondary="task_tags", back_populates="tags")

    __table_args__ = (UniqueConstraint('name', 'user_id', 'team_id', name='uix_tag_name_user_team'),)

class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id = Column(Integer, ForeignKey("tasks.task_id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.tag_id"), primary_key=True)
