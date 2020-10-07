CINEMAS = {
    "City": 1,
    "Groningen": 4,
    "De Munt": 10,
    "Arnhem": 27,
    "Zwolle": 28,
}

PATHE_URL = "https://www.pathe.nl"
PATHE_UPDATE_LOC = "/update-schedule/"

PATHE_BS4_MOVIE_LIST = ["div", {"class": "schedule__section"}]
PATHE_BS4_MOVIE_TIME = ["a", {"class": "schedule-time"}]