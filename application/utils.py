from datetime import date
from datetime import datetime


def get_current_date():
    return str(date.today().strftime("%d-%m-%Y"))


def get_sched_duration(start, end):
    start_time = datetime.strptime(start[:-6], "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.strptime(end[:-6], "%Y-%m-%dT%H:%M:%S")
    tdelta = end_time - start_time
    return f"{str(tdelta.total_seconds() / 60)[:-2]}"  # Get total minutes and slice off trailing decimal

def get_sched_time(time_str):
    return f"{time_str[11:-6]}"