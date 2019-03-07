from models.base import Base, engine
from models.metadata_registry import MetadataRegistry

print(Base.metadata.create_all(engine))
