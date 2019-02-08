from base import Base, engine
from metadata_registry import MetadataRegistry

print(Base.metadata.create_all(engine))
