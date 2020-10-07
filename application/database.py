from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine('sqlite:///webserver.db')
Base = declarative_base()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True)
    start_time = Column(String)
    ticket_href = Column(String)
    soldout = Column(Boolean)
    seats_available = Column(Integer, default=0)
    seats_total = Column(Integer, default=0)
    cinema = Column(String)

    movie_id = Column(Integer, ForeignKey('movies.id'))
    movie = relationship("Movie", back_populates="schedules")

    def __repr__(self):
        return f"<Schedule(Starting at {self.start_time} in {self.cinema} Available: {self.seats_available})>"


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # Let's hope Pathe doesn't mess up
    duration = Column(Integer)

    schedules = relationship("Schedule", order_by=Schedule.id, back_populates="movie")

    def __repr__(self):
        return f"<Movie({self.name}, duration {self.duration} minutes)>"
