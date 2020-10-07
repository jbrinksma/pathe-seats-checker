import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from optparse import OptionParser
import sys
import flask

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


pathe_locations = {
    "Arena": 9,
    "Groningen": 4,
    "Zwolle": 28,
    "Arnhem": 27
}

PATHE_URL = "https://www.pathe.nl"


def get_seats(ticket_href):
    seats_total = 0
    seats_available = 0

    try:
        req = requests.post(PATHE_URL + ticket_href)  # Get special URL redirection
        req = requests.get(req.url + "/stoelen")
    except Exception:
        return seats_available, seats_total  # Some error occurred during web request.

    if ticket_href in req.url:
        return seats_available, seats_total  # Most likely you can't buy tickets anymore because the movie started.
    if req.status_code == 404:
        return seats_available, seats_total  # Most likely you can't buy tickets anymore because the movie started.
    if req.status_code == 500:
        return seats_available, seats_total  # Most likely there are no seats for this movie. (Known possibility: Drive-In Cinema)

    soup = BeautifulSoup(req.text, "html.parser")
    try:
        seats = soup.findChild("ul", {"id": "seats"}).findChildren("li")
    except AttributeError:  # Unknown error..
        print("\nError at:")
        print(req.status_code)
        print(req.url)
        print("")
        return seats_available, seats_total

    for seat in seats:
        seats_total += 1
        try:
            seat["class"]
        except KeyError:
            seats_available += 1
    return seats_available, seats_total


class MovieStartTime:
    def __init__(self, start_time, ticket_href, soldout, location):
        self.start_time = start_time
        self.ticket_href = ticket_href
        self.soldout = soldout
        self.seats_available, self.seats_total = get_seats(ticket_href)
        self.location = location
    
    def __repr__(self):
        return self.start_time

    def __str__(self):
        return self.start_time


def get_movie_start_times(soup_movie):
    return [MovieStartTime(
            start_time = time.findChild("span", {"class": "schedule-time__start"}).find(text=True),
            ticket_href = time["data-href"],
            soldout = time["data-soldout"],  # Keep this?
            location = get_movie_location_of_start_time(time)
        ) for time in soup_movie.findChildren("a", {"class": "schedule-time"})  # if time["data-soldout"] != "True"
    ]


def get_movie_name(soup_movie):
    return soup_movie.findChild("figcaption", {"class": "schedule__article"}).findChild("a")["title"]


def get_movie_duration(soup_movie):
    start_time = soup_movie.findChild("span", {"class": "schedule-time__start"}).find(text=True)
    end_time = soup_movie.findChild("span", {"class": "schedule-time__end"}).find(text=True)
    tdelta = datetime.strptime(end_time, "%H:%M") - datetime.strptime(start_time, "%H:%M")
    return f"{str(tdelta.total_seconds() / 60)[:-2]}"


def get_movie_locations(soup_movie):
    return [soup_location.find(text=True) for soup_location in soup_movie.findChildren("p", {"class": "schedule__location"})]

def get_movie_location_of_start_time(soup_schedule_time):
    return soup_schedule_time.findParent().findPreviousSibling().find(text=True)

class Movie:
    def __init__(self, soup_movie):
        self.name = get_movie_name(soup_movie)
        self.duration = get_movie_duration(soup_movie)
        self.schedule = get_movie_start_times(soup_movie)
        self.locations = get_movie_locations(soup_movie)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def get_movies(soup):
    movie_elements = soup.find_all("div", {"class": "schedule__section"})
    return [element.findChild("figcaption", {"class": "schedule__article"}).findChild("a")["title"] for element in movie_elements]


def get_info_movies(locations:list, movie_names:list, date):
    url = PATHE_URL + "/update-schedule/" + format_loc_str(locations) + "/" + date
    try:
        req = requests.get(url)
    except Exception:
        sys.exit("Failed to connect to Pathe website.")
    page = req.text
    soup = BeautifulSoup(page, "html.parser")

    list_of_movies = []
    # print(f"{bcolors.WARNING}Als een locatie niet bij een film staat, dan draait de film daar niet (meer) op die dag.{bcolors.ENDC}\n")
    for item in soup.find_all("div", {"class": "schedule__section"}):

        for movie in movie_names:
            if movie.lower() in item.findChild("figcaption", {"class": "schedule__article"}).findChild("a")["title"].lower():
                break
        else:
            continue

        
        list_of_movies.append(Movie(item))
        # print(f"Film: {bcolors.OKGREEN}{mov}{bcolors.ENDC}  -  (duurt {bcolors.OKBLUE}{mov.duration} minuten{bcolors.ENDC})")
        # for location in mov.locations:
        #     print(f"    {location}")
        #     for item in mov.schedule:
        #         if item.location == location:
        #             break
        #     else:
        #         print(f"        {bcolors.BOLD}DRAAIT NIET{bcolors.ENDC}")
        #         continue
        #     for item in mov.schedule:
        #         if item.location == location:
        #             if item.soldout == "True":
        #                 print(f"        Start om: {item.start_time}  -  {bcolors.FAIL}Uitverkocht :({bcolors.ENDC}")
        #             elif item.seats_total <= 0:
        #                 print(f"        Start om: {item.start_time}  -  {bcolors.FAIL}Kan geen tickets meer krijgen :({bcolors.ENDC}")
        #             elif item.seats_available <= 0:
        #                 print(f"        Start om: {item.start_time}  -  ({bcolors.FAIL}stoelen vrij: {item.seats_available}/{item.seats_total}{bcolors.ENDC})")
        #             elif item.seats_available <= 40:
        #                 print(f"        Start om: {item.start_time}  -  ({bcolors.WARNING}stoelen vrij: {item.seats_available}/{item.seats_total}{bcolors.ENDC})")
        #             else:
        #                 print(f"        Start om: {item.start_time}  -  (stoelen vrij: {item.seats_available}/{item.seats_total})")
        #     print("")
        # print("")
    return list_of_movies

# def main(locations:list, date:str):
    
# TODO: Hoeveel personen, naast elkaar mogelijk?
# TODO: Soort film (2D, 3D etc)
# TODO: Python logging

def optionparser():
    parser = OptionParser()
    parser.add_option("--locaties", type=str, dest="locations", metavar="LOC1,LOC2", help="Voorbeeld: --locaties=Arena,Zwolle (Kies uit: Arena, Zwolle, Groningen, Arnhem) (Er wordt gescheiden op komma's)")
    parser.add_option("--films", type=str, dest="movies", metavar="\"FILMNAAM 1,FILMNAAM 2\"", help="Hoeft niet volledige naam te zijn. Gebruik aanhalingstekens. Voorbeeld: --films=\"Pirates Of The,Toy Sto\" (Er wordt gescheiden op komma's)")
    parser.add_option("--datum", type=str, dest="date", metavar="DD-MM-YYYY", help="Voorbeeld: 03-10-2020")
    return parser.parse_args()


if __name__ == "__main__":
    (options, args) = optionparser()
    if not options.locations or not options.movies or not options.date:
        sys.exit("Please supply all options.")

    locations = options.locations.split(",")
    locations_ints = []
    for loc in locations:
        if loc not in pathe_locations:
            sys.exit(f"Locatie is niet ondersteund: {loc}")
        else:
            locations_ints.append(pathe_locations[loc])

    get_info_movies(locations_ints, options.movies.split(","), options.date)
