import datetime
import guessit
import logging
logger = logging.getLogger(__file__)

from sqlalchemy import Integer, String, Column, create_engine, DateTime, ForeignKey, Boolean, Interval, SmallInteger, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = create_engine("sqlite:///movies.db", echo=True)
Session = sessionmaker(bind=engine)


class Movie(Base):
    __tablename__ = "movie"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(Date)
    year = Column(SmallInteger)
    status = Column(Integer)
    paused = Column(Boolean, default=False)
    start = Column(Interval, default=datetime.timedelta(days=-7))
    interval = Column(Interval, default=datetime.timedelta(days=1))
    added = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    completed = Column(DateTime)
    searched = Column(DateTime)

    result = relationship("Result", uselist=False, back_populates="movie")
    results = relationship("Result", back_populates="movie")

    external_ids = relationship("ExternalID", back_populates="movie")

    def __init__(self, name: str, date: datetime.date):
        self.name = name
        self.date = date

    def __repr__(self):
        return f"{self.name}"


class Result(Base):
    __tablename__ = "result"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    title = Column(String)
    url = Column(String)
    size = Column(Integer)
    year = Column(SmallInteger)
    provider = Column(String)
    seeders = Column(Integer)
    leechers = Column(Integer)
    group = Column(String)
    type = Column(String)
    found = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)

    movie_id = Column(Integer, ForeignKey('movie.id'))
    movie = relationship("Movie", back_populates="result")

    session = Session()

    def __init__(self, name: str, url: str, seeders: int, leechers: int, size: int, type=None):
        guess = guessit.guessit(name)
        if not (guess and guess["type"] == "movie"):
            logging.debug(f"This is an episode, not a movie: {name}")
            return

        if not self.session.query(Movie).filter(Movie.name.like(f"{guess['title']}%")).count():
            logging.debug(f"This result does not match any of our movies")
            return

        if not type:
            if url.startswith('magnet') or url.endswith('.torrent'):
                type = 'torrent'
            elif url.endswith('.nzb'):
                type = 'nzb'
            else:
                logging.debug(f"Cannot determine the type of download for {url}")
                return

        self.url = url
        self.name = name
        self.title = guess["title"]
        self.group = guess["release_group"]
        self.seeders = seeders
        self.leechers = leechers
        self.size = size
        self.year = guess["year"]
        self.type = type

    def __repr__(self):
        return f"{self.name}"


class ExternalID(Base):
    __tablename__ = "external_id"
    id = Column(Integer, primary_key=True)
    site = Column(String)

    movie_id = Column(Integer, ForeignKey('movie.id'))
    movie = relationship("Movie", back_populates="external_ids")


Base.metadata.create_all(engine, checkfirst=True)
