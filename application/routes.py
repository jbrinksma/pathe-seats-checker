import requests
from flask import request, render_template

from . import app
from .database import Session, Movie, Schedule
from .utils import get_current_date
from .logger import log_warn


#
# Don't worry, I made this list comprehension atrocity on purpose.
#
def database_to_frontend(session):
    db_movies = session.query(Movie).all()
    db_schedules = session.query(Schedule).all()
    
    movies = [[{"name": db_mov.name, "duration": db_mov.duration}, list()] for db_mov in db_movies]
    for mov in movies:
        unique_cinemas = []
        for db_sched in db_schedules:
            if mov[0]["name"] == db_sched.movie.name and db_sched.cinema not in unique_cinemas:
                unique_cinemas.append(db_sched.cinema)

        mov[1] = [[cinema, [{
            "start_time": sched.start_time,
            "seats_available": sched.seats_available,
            "seats_total": sched.seats_total,
            "soldout": sched.soldout,
        } for sched in db_schedules if mov[0]["name"] == sched.movie.name and cinema == sched.cinema]] for cinema in unique_cinemas]

    movies.sort(key=lambda e: e[0]["name"])  # Sort on movie name

    # for movie in movies:
    #     print(f"{movie[0]['name']}")
    #     for cinema in movie[1]:
    #         print(f"    {cinema[0]}")
    #         for schedule in cinema[1]:
    #             print(f"        {schedule['seats_available']}")
    return movies


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

    data = database_to_frontend(Session)
    Session.remove()

    return render_template('index.html', data=data, date=get_current_date())