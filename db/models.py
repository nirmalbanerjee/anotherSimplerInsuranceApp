from sqlalchemy import Column, Integer, String, Text
from .database import Base

class UserORM(Base):
    __tablename__ = "users"
    username = Column(String(100), primary_key=True, index=True)
    password = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False)

class PolicyORM(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    owner = Column(String(100), nullable=False)