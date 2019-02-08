from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean, String
from models.base import Base

class MetadataRegistry(Base):
    __tablename__ = 'metadata_registry'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    status = Column(Boolean(name='ck_status_bool'))

