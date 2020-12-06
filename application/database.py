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

    pathe_sched_id = Column(Integer)

    start_time = Column(String)
    end_time = Column(String)

    soldout = Column(Boolean)

    cinema_name = Column(String)
    movie_name = Column(String)

    seats_available = Column(Integer, default=0)
    seats_total = Column(Integer, default=0)

    def __repr__(self):
        return f"<Schedule({self.movie_name} in {self.cinema_name} Starting at {self.start_time} Available: {self.seats_available})>"

