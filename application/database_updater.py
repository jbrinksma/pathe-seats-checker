from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import requests
import sys
from bs4 import BeautifulSoup
from threading import Thread
import time
import sqlalchemy

from .utils import format_cinema_num_str, get_current_date
from .config import (
    CINEMAS,
    PATHE_URL,
    PATHE_UPDATE_LOC,
    PATHE_BS4_MOVIE_LIST,
    PATHE_BS4_MOVIE_TIME
)
from .soup_parsing import (
    get_movie_name_from_soup,
    get_movie_duration_from_soup,
    get_movie_location_from_soup
)
from .logger import log_info, log_warn, log_err
from .database import Schedule, Movie, Session


def start_db_updater():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=job_update_movie_list_and_schedules, trigger="interval", seconds=30)
    scheduler.add_job(func=job_update_total_seats_per_movie, trigger="interval", seconds=600)
    scheduler.start()
    log_warn("Periodical update jobs are scheduled.")
    atexit.register(lambda: scheduler.shutdown())
    atexit.register(lambda: log_warn("Application has shutdown."))


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
        if schedule.soldout:
            continue
        # Using the schedule.ticket_href attribute as a reference for the worker is probably safer,
        # than using the schedule.id attribute, since during execution of the thread, the
        # Schedule we want to refer to might have been deleted, and SQLite might have re-used
        # the id for a new Schedule object in the database.
        # 
        # The href value, however, stays unique, and
        # is always connected through Pathe to the original Schedule data.
        schedule_ticket_href = schedule.ticket_href

        t = Thread(target=update_seats_worker, args=[schedule_ticket_href, schedule.movie.name])
        threads.append(t)
        t.start()
        time.sleep(1)  # Relax
    

    for t in threads:  # Wait untill all threads finish
        t.join()
    Session.remove()
    log_warn("All threads finished.")


def update_seats_worker(schedule_ticket_href, movie_name):
    try:
        # Get the Schedule object from a thread-local session with the db.
        schedule = Session.query(Schedule).filter_by(ticket_href=schedule_ticket_href).first()
        if not schedule:
            log_err(f"Thread: failed to update movies and schedules: schedule was deleted during thread execution")
        else:
            update_seats_in_thread(Session, schedule, movie_name)
    except sqlalchemy.exc.OperationalError as e:
        log_err(f"Thread: failed to update movies and schedules: database error: {e}")
    finally:
        Session.remove()


def update_seats_in_thread(session, schedule, movie_name):  # Asking for movie relationship within thread causes problems
    try:
        req = requests.post(PATHE_URL + schedule.ticket_href)  # Get special URL redirection
        req = requests.get(req.url + "/stoelen")
    except Exception:
        log_err(f"Thread: seat update failed because of request error")
        return  # Some error occurred during web request.

    if schedule.ticket_href in req.url or req.status_code != 200:
        if req.status_code != 200:
            log_err(f"Thread: seat update failed because of bad status code: {req.status_code} Movie: {schedule.cinema} - {schedule.start_time} - {movie_name}")
        return  # Most likely you can't buy tickets anymore because the movie started.
                # If 500: Most likely there are no seats for this movie. (Known possibility: Drive-In Cinema)

    soup = BeautifulSoup(req.text, "html.parser")

    try:
        seats = soup.findChild("ul", {"id": "seats"}).findChildren("li")
    except AttributeError:  # Unknown error..
        log_err(f"Thread: seat update failed during html parsing: did the website structure change?")
        return
    
    seats_available = 0
    for seat in seats:
        try:
            seat["class"]
        except KeyError:  # Only occupied seats seem to have a class defined
            seats_available += 1
    
    schedule.seats_total = len(seats)
    schedule.seats_available = seats_available
    session.add(schedule)


def job_update_movie_list_and_schedules():
    try:
        update_movie_list_and_schedules(Session)
    except sqlalchemy.exc.OperationalError as e:
        log_err(f"Failed to update movies and schedules: database error: {e}")
    finally:
        Session.remove()


def update_movie_list_and_schedules(session):
    cinemas = [cinema for cinema in CINEMAS]
    req_url = PATHE_URL + PATHE_UPDATE_LOC + format_cinema_num_str(cinemas) + get_current_date()

    log_warn(f"Running movie/schedule updater (URL: {req_url})")
    try:
        req = requests.get(req_url)
    except Exception:
        log_err("Failed to reach Pathe movie listing.")

    
    # TODO: IF STATUS CODE NOT....

    # TODO: If not None.....
    soup = BeautifulSoup(req.text, "html.parser")

    movies_found = []

    for soup_movie in soup.find_all(PATHE_BS4_MOVIE_LIST[0], PATHE_BS4_MOVIE_LIST[1]):
        movie_name = get_movie_name_from_soup(soup_movie)
        movie_duration = get_movie_duration_from_soup(soup_movie)

        movies_found.append(movie_name)

        movie = session.query(Movie).filter_by(name=movie_name).first()
        log_info(f"Movie exists in db: {movie_name}")
        if not movie:
            movie = Movie(name=movie_name, duration=movie_duration)
            log_warn(f"New movie found: {movie_name}")

        schedules_found = []
        
        try:
            schedules_in_db = session.query(Schedule).filter_by(movie=movie).all()
        except Exception:  # Movie doesn't exist yet
            schedules_in_db = []

        for soup_time in soup_movie.findChildren(PATHE_BS4_MOVIE_TIME[0], PATHE_BS4_MOVIE_TIME[1]):
            start_time = soup_time.findChild("span", {"class": "schedule-time__start"}).find(text=True)
            cinema = get_movie_location_from_soup(soup_time)

            schedules_found.append([start_time, cinema])

            if schedules_in_db:
                exists = False
                for schedule in schedules_in_db:
                    if schedule.start_time == start_time and schedule.cinema == cinema:
                        exists = True
                        break
                if exists:
                    log_info(f"Schedule exists in db: {movie} - {cinema} - {start_time}")
                    continue
            
            schedule = Schedule(
                start_time = start_time,
                ticket_href = soup_time["data-href"],
                soldout = True if soup_time["data-soldout"] == "True" else False,
                cinema = cinema
            )
        
            log_warn(f"New schedule found for {cinema} - {movie_name} - starts {schedule.start_time}")
            movie.schedules.append(schedule)

        for db_sched in schedules_in_db:
            exists = False
            for schedule in schedules_found:
                if schedule[0] == db_sched.start_time and schedule[1] == db_sched.cinema:
                    exists = True
                    break
            if exists == False:
                log_warn(f"Deleting schedule from db which is not on website anymore: {movie.name} - {db_sched.cinema} - {db_sched.start_time}")
                session.delete(db_sched)

        session.add(movie)

    movies_in_db = session.query(Movie).all()
    for movie in movies_in_db:
        if movie.name not in movies_found:
            log_warn(f"Deleting movie from db which is not on website anymore: {movie.name}")
            for schedule in movie.schedules:
                session.delete(schedule)
            session.delete(movie)

    session.commit()