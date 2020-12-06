from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import requests
import sys
from bs4 import BeautifulSoup
from threading import Thread
import time
import sqlalchemy

from pathe_api import PatheApi
from pathe_api.exceptions import PatheApiException

from .utils import get_current_date, get_sched_duration, get_sched_time
from .config import (
    CINEMAS,
    PATHE_URL,
    PATHE_UPDATE_LOC,
    PATHE_BS4_MOVIE_LIST,
    PATHE_BS4_MOVIE_TIME
)
from .logger import log_info, log_warn, log_err
from .database import Schedule, Session


def start_db_updater():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=job_update_movie_list_and_schedules, trigger="interval", seconds=30)
    scheduler.add_job(func=job_update_total_seats_per_movie, trigger="interval", seconds=600)
    scheduler.start()
    log_warn("Periodical update jobs are scheduled.")
    atexit.register(lambda: scheduler.shutdown())
    atexit.register(lambda: log_warn("Application has shut down."))


def job_update_total_seats_per_movie():
    log_warn(f"Running threaded Seats Updater.")

    try:
        schedules = Session.query(Schedule).all()
    except Exception:
        log_err("No schedules found in database.")
        Session.remove()
    
    threads = []
    log_warn("Creating Threads and waiting for them all to finish...")
    for schedule in schedules:
        t = Thread(target=update_seats_worker, args=[schedule.pathe_sched_id])
        threads.append(t)
        t.start()
        time.sleep(0.1)  # Relax
    
    for t in threads:  # Wait untill all threads finish
        t.join()
    Session.remove()
    log_warn("All threads finished.")


def update_seats_worker(pathe_sched_id):
    try:
        # Get the Schedule object from a thread-local session with the db.
        schedule = Session.query(Schedule).filter_by(pathe_sched_id=pathe_sched_id).first()
        if not schedule:
            log_err(f"Thread: failed to update movies and schedules: schedule was deleted during thread execution")
        else:
            update_seats_in_thread(Session, schedule)
    except sqlalchemy.exc.OperationalError as e:
        log_err(f"Thread: failed to update movies and schedules: database error: {e}")
    finally:
        Session.remove()


def update_seats_in_thread(session, schedule):  # Asking for movie relationship within thread causes problems
    api = PatheApi()
    try:
        pathe_seats = api.get_seats(schedule.pathe_sched_id)
    except PatheApiException as e:
        log_err(f"Thread: seat update failed in api call: {e}")
        return  # Some error occurred during web request.

    schedule.seats_total = api.count_total_seats(pathe_seats)
    schedule.seats_available = api.count_available_seats(pathe_seats)
    session.add(schedule)
    session.commit()


def job_update_movie_list_and_schedules():
    try:
        update_movie_list_and_schedules(Session)
    except sqlalchemy.exc.OperationalError as e:
        log_err(f"Failed to update movies and schedules: database error: {e}")
    finally:
        Session.remove()


def get_cinema_name_by_id(id, cinemas):
    for cinema in cinemas:
        if cinema.id == id:
            return cinema.name
    else:
        return None


def update_movie_list_and_schedules(session):
    log_warn(f"Running movie/schedule updater")
    api = PatheApi()
    try:
        cinemas = api.get_cinemas()
        timetable = api.get_timetable(cinemas)
    except PatheApiException as e:
        log_err(f"Failed to reach Pathe movie listing: {e}")
        return
    
    try:
        schedules_in_db = session.query(Schedule).all()
    except Exception as e:
        log_err(f"Failed to get database content: {e}")
        return

    for db_sched in schedules_in_db:
        for tt_sched in timetable.schedules:
            if tt_sched.id == db_sched.pathe_sched_id:
                break
        else:
            log_warn(f"Removing {db_sched}")
            session.delete(db_sched)

    for tt_sched in timetable.schedules:
        for db_sched in schedules_in_db:
            if tt_sched.id == db_sched.pathe_sched_id:
                break
        else:
            session.add(Schedule(
                pathe_sched_id = tt_sched.id,
                start_time = get_sched_time(tt_sched.start),
                end_time = get_sched_time(tt_sched.end),
                soldout = True if "Uitverkocht" in tt_sched.tag else False,
                cinema_name = get_cinema_name_by_id(tt_sched.cinema_id, cinemas),
                movie_name = tt_sched.movie_name,
                seats_available = 0,
                seats_total = 0
            ))


    # if not anymore delete

    session.commit()