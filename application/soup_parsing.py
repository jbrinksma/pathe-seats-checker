from datetime import datetime


def get_movie_name_from_soup(soup_movie:"Soup item of PATHE_BS4_MOVIE_LIST"):
    return soup_movie.findChild("figcaption", {"class": "schedule__article"}).findChild("a")["title"]


def get_movie_duration_from_soup(soup_movie):
    start_time = soup_movie.findChild("span", {"class": "schedule-time__start"}).find(text=True)
    end_time = soup_movie.findChild("span", {"class": "schedule-time__end"}).find(text=True)
    tdelta = datetime.strptime(end_time, "%H:%M") - datetime.strptime(start_time, "%H:%M")
    return f"{str(tdelta.total_seconds() / 60)[:-2]}"  # Get total minutes and slice off trailing decimal


def get_movie_location_from_soup(soup_time):
    return soup_time.findParent().findPreviousSibling().find(text=True)