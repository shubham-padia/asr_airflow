from models.base import Base, engine
from models.metadata_registry import MetadataRegistry

print(Base.metadata.create_all(engine))

from alembic.config import Config
from alembic import command
alembic_cfg = Config("alembic.ini")
command.stamp(alembic_cfg, "head")

# create connection
from airflow import settings
from airflow.models import Connection
from envparse import env

env.read_envfile()
conn = Connection(
    conn_id='watcher',
    conn_type='Postgres',
    host='localhost',
    login=env('WATCHER_LOGIN', default='watcher'),
    password=env('WATCHER_PASSWORD', default='watcher_prod'),
    port=5432
) #create a connection object
session = settings.Session() # get the session
session.add(conn)
session.commit()