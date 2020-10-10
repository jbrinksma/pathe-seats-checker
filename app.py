#!/usr/bin/python3
from waitress import serve

from application import app
from application.logger import log_warn
from application.database_updater import (
    job_update_movie_list_and_schedules,
    job_update_total_seats_per_movie,
    start_db_updater
)
from application.database import Base, engine

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    # TODO: Movies without Seats jinja templating
    # TODO: Db checks try/except
    # TODO: Fix killed server during job schedule
    # TODO: Seat changes logging
    # TODO: Thread request delay for more cinemas (put in config)
    # TODO: If threads takes longer than x... CANT KEEP UP
    # TODO: Wait for jobs upon application exit
    # TODO: Remove movie if no elements after filter? Or say no movies?
    # TODO: Not initialized yet == Kan geen tickets meer krijgen
    # TODO: Percentage wise warnings seats?
    # TODO: What happens when object is deleted in different scoped session
    print("Starting the application -- Welcome!")
    log_warn("Starting the application -- Welcome!")
    # Update all before starting server
    print("Updating database... (this may take a couple minutes)")
    job_update_movie_list_and_schedules()
    job_update_total_seats_per_movie()
    print("Done")
    # Start background update jobs
    start_db_updater()
    print("Starting the webserver")
    log_warn("Starting the webserver")
    serve(app, port=80, threads=100)
