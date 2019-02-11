from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean, String, DateTime
from sqlalchemy.sql import func
from models.base import Base
import datetime

class MetadataRegistry(Base):
    __tablename__ = 'metadata_registry'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    status = Column(Boolean(name='ck_status_bool'))
    
    # Make sure you aren't using default=datetime.datetime.utcnow(); you want
    # to pass the utcnow function, not the result of evaluating it at module
    # load.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __init__(self, filename, status=False):
        self.filename = filename
        self.status = status
