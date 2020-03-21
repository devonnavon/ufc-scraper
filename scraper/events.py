import scraper
import json
import os
from pathlib import Path


EVENTS_URL = 'http://ufcstats.com/statistics/events/completed?page=all'
BASE_PATH = Path(os.getcwd())/'data'
EVENTS = BASE_PATH/'events.json'

def get_events(events_url: str=EVENTS_URL):# -> Dict[str, List[str]]:
    '''
    get completed events dictionary
    '''
    events = []
    soup = scraper.make_soup(events_url)
    table_data = soup.findAll('td',{'class': 'b-statistics__table-col'})
    #below groups data by rows, table_rows is a list of tuples each tuple corresponding to a row
    table_rows = list(zip(table_data,table_data[1:]))[::2] 
    for row in table_rows:
        #row[0] has event data row[1] has location 
        link = row[0].find('a')
        event_id = link.get('href').split('/')[-1]
        event_name = link.text.strip()
        event_date = row[0].find('span').text.strip() ###maybe convert to datetime here?
        event_location = row[1].text.strip()
        events.append({
            'id':event_id,
            'name':event_name,
            'date':event_date,
            'location':event_location
        })
    return events