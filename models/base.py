from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(
        'postgresql://watcher:yeshallnotpass@localhost:5432/watcher')
Session = sessionmaker(bind=engine)

Base = declarative_base(engine)
