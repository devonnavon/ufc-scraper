import pandas as pd

import scraper
from scraper import events, fights, fighters

if __name__ == "__main__":
    event_ids = events.load_events() #load events returns new event_ids that were loaded
    fights.load_fights(event_ids)
    if len(event_ids) != 0: #if events is greater than 0 we need to update fighters
        fighters.load_fighters()
    else:
        print("no fighters were updated")

