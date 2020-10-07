from datetime import date
from .config import CINEMAS


def get_current_date():
    return str(date.today().strftime("%d-%m-%Y"))


def format_cinema_num_str(cinemas:"List of dictionary entries (name:int)"):
    cinema_num_str = ""
    for cinema in cinemas:
        cinema_num_str += f"{CINEMAS[cinema]},"
    return cinema_num_str[:-1] + "/"
