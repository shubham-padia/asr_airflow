from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from envparse import env

env.read_envfile()

engine = create_engine(env('WATCHER_DB_URL'))
Session = sessionmaker(bind=engine)

Base = declarative_base(engine)
