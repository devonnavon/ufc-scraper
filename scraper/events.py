import json
import os
from pathlib import Path
from datetime import datetime
from dateutil import parser
from typing import List, Dict, Tuple

import scraper


EVENTS_URL = 'http://ufcstats.com/statistics/events/completed?page=all'
BASE_PATH = Path(os.getcwd())/'data'
EVENTS_PATH = BASE_PATH/'events.json'

def get_events(events_url: str=EVENTS_URL) -> List[str]:
    '''
    get completed events dictionary
    scrapes home page of ufcstats.com to get completed events
    does a check to ensure only events that have happened date<today
    '''
    events = []
    soup = scraper.make_soup(events_url)
    table_data = soup.findAll('td',{'class': 'b-statistics__table-col'})
    #below groups data by rows, table_rows is a list of tuples each tuple corresponding to a row
    table_rows = list(zip(table_data,table_data[1:]))[::2] 
    for row in table_rows:
        #row[0] has event data row[1] has location 
        event_date = parser.parse(row[0].find('span').text.strip()) #convert to datetime
        if event_date > datetime.today():
            continue
        link = row[0].find('a')
        event_id = link.get('href').split('/')[-1]
        event_name = link.text.strip()
        event_location = row[1].text.strip()
        events.append({
            'id':event_id,
            'name':event_name,
            'date':event_date, #convert to str for json
            'location':event_location
        })
    return events

def load_events() -> List[str]:
    '''
    loads events dict into data/events.json
    returns all event_ids that weren't already loaded 
    '''
    events_dict = get_events(EVENTS_URL) #scrape events
    new_ids = [event['id'] for event in events_dict] #extract ids
    #check if data/events.json exists, build and dump if it doesn't
    if not os.path.exists(EVENTS_PATH): 
        with open(EVENTS_PATH, 'w') as f:
            f.write(json.dumps(events_dict, indent=4, default=str))
        return new_ids
    #if it does exist we still replace everything in the file but only return ids we didn't have
    else:
        with open(EVENTS_PATH, 'r') as f: #open in read mode
            current_events_dict = json.load(f)
        with open(EVENTS_PATH, 'w') as f: #open in write and replace everything
            f.write(json.dumps(events_dict, indent=4, default=str))
        current_ids = [event['id'] for event in current_events_dict] #get_currently loaded ids
        return list(set(new_ids) - set(current_ids)) #only return ids we didn't already have

