import requests
from flask import request, render_template

from . import app
from .database import Session, Schedule
from .utils import get_current_date
from .logger import log_warn


class FrontendSchedule:
    def __init__(self, db_sched):
        self.movie_name = db_sched.movie_name
        self.cinema_name = db_sched.cinema_name
        self.start_time = db_sched.start_time
        self.end_time = db_sched.end_time
        self.soldout = db_sched.soldout
        self.seats_available = db_sched.seats_available
        self.seats_total = db_sched.seats_total


class FrontendCinema:
    def __init__(self, db_schedules, cinema_name, movie_name):
        self.name = cinema_name
        self.schedules = [FrontendSchedule(sched) for sched in db_schedules if sched.cinema_name == cinema_name and sched.movie_name == movie_name]


class FrontendMovie:
    def __init__(self, db_schedules, movie_name):
        self.name = movie_name

        cinemas = []
        for sched in db_schedules:
            if sched.cinema_name not in cinemas:
                cinemas.append(sched.cinema_name)
        cinemas.sort()
        temp_cinemas = [FrontendCinema(db_schedules, cinema, movie_name) for cinema in cinemas]
        self.cinemas = [cinema for cinema in temp_cinemas if cinema.schedules]


def database_to_frontend(db_schedules):
    movies = []
    for sched in db_schedules:
        if sched.movie_name not in movies:
            movies.append(sched.movie_name)
    return [FrontendMovie(db_schedules, movie) for movie in movies]


@app.context_processor
def inject_current_date():
    return dict(current_date=get_current_date())

@app.route("/", methods=["GET"])
def root():
    try:
        location = requests.get("https://extreme-ip-lookup.com/json/" + request.remote_addr).json()["city"]
    except Exception:
        location = "FAILED TO GET LOCATION"
    log_warn(f"Incoming request from {request.remote_addr} in {location}")

    db_schedules = Session.query(Schedule).all()
    Session.remove()

    movies = database_to_frontend(db_schedules)

    return render_template('index.html', movies=movies, date=get_current_date())