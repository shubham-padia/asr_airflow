from models.base import Base, engine
from models.metadata_registry import MetadataRegistry

print(Base.metadata.create_all(engine))

from alembic.config import Config
from alembic import command
alembic_cfg = Config("alembic.ini")
command.stamp(alembic_cfg, "head")
