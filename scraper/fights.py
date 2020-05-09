import json
import os
import multiprocessing
import threading
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple

import scraper

BASE_PATH = Path(os.getcwd())/'data'
FIGHTS_PATH = BASE_PATH/'fights.json'

EVENT_URL = 'http://ufcstats.com/event-details/{event_id}'
FIGHT_URL = 'http://ufcstats.com/fight-details/{fight_id}'

FIGHT_HEADER = '''r_fighter;b_fighter;r_kd;b_kd;r_sig_str.;b_sig_str.;r_sig_str_pct;b_sig_str_pct;r_total_str.;b_total_str.;r_td;b_td;r_td_pct;b_td_pct;r_sub_att;b_sub_att;r_pass;b_pass;r_rev;b_rev;r_head;b_head;r_body;b_body;r_leg;b_leg;r_distance;b_distance;r_clinch;b_clinch;r_ground;b_ground;win_by;last_round;last_round_time;format;referee;fight_type;winner'''


def load_fights(event_ids:str):
    '''
    loads all fights for list of event_ids into data/fights.json
    appends if fights already there
    '''
    #scrape the fight data
    all_fight_info = []
    l = len(event_ids)
    print('Scraping all fight data: ')
    scraper.print_progress(0, l, prefix = 'Progress:', suffix = 'Complete')
    for i,event_id in enumerate(event_ids): 
        all_fight_info += get_event_fights(event_id)
        scraper.print_progress(i + 1, l, prefix = 'Progress:', suffix = 'Complete')
    #load into json
    if not os.path.exists(FIGHTS_PATH): #if file doesn't exist
        with open(FIGHTS_PATH, 'w') as f:
            f.write(json.dumps(all_fight_info, indent=4, default=str))
    else: #if it does we update and dump
        with open(FIGHTS_PATH, 'r+') as f:
            old_data = json.load(f)
            f.seek(0)
            f.write(json.dumps(all_fight_info+old_data, indent=4, default=str))
    print(len(all_fight_info), ' fights loaded into ', str(FIGHTS_PATH))

def get_event_fights(event_id: str) -> List[Dict[str,str]]:
    '''
    gets all fight info for every fight in an event
    '''
    fight_ids = get_fight_ids(event_id) #get list of fight ids
    fights_info = get_fights(fight_ids)  #fight info =[{},{}]
    for fight in fights_info:
        fight.update({'event_id': event_id})
    return fights_info

def get_fights(fight_ids:List[str]) -> List[Dict[str,str]]:
    '''
    gets all fight data for a given event id using multi threading
    checks for server error (result of too many concurrent requests)
        if there are server errors waits for running requests to finish
        then runs get_fights recursively 
    returns dict {event_id:[{fight_info},{fight_info}...]}
    '''
    #below we create a pool to scrape each fight for an event in parallel 
    q = multiprocessing.Queue() #queue to store the results
    t = {} #dict to hold our threads
    results = []

    #wrapper function to populate queue
    def put_fight_info(fight_id):
        fight_info = get_fight_info(fight_id)
        q.put(fight_info)

    for fight_id in fight_ids: #this starts a thread for every fight_id
        t[fight_id] = threading.Thread(target=put_fight_info, args=(fight_id,))
        t[fight_id].start()

    for thread in t: #join closes out the threads (i think)
        t[thread].join() 
        
    while not q.empty():
        queue_top = q.get()
        results.append(queue_top)
    
    errored_ids = []
    good_results = []
    for result in results:
        if result['err'] == 'Server Too Busy': 
            errored_ids.append(result['fight_id']) 
        elif result['err'] is None:
            del result['err']
            good_results.append(result)
        else:
            pass #if theres another error we just don't include this fight

    if len(errored_ids) > 0: #if there are errored ids we remove these and try again
        good_results+= get_fights(errored_ids)

    return good_results

def get_fight_ids(event_id:str) -> List[str]:
    '''
    from list of event_ids returns dict with {event_id:[fight_id, fight_id,...]}
    '''
    soup = scraper.make_soup(EVENT_URL.format(event_id=event_id))
    fight_ids = []
    for row in soup.findAll('tr',{'class':'b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click'}):
        fight_ids.append(row.get('data-link').split('/')[-1])
    return fight_ids

def get_fight_info(fight_id:str) -> Dict[str,str]:
    fight_soup = scraper.make_soup(FIGHT_URL.format(fight_id=fight_id)) 
    try: 
        fight_stats = get_fight_stats(fight_soup) #err
    except:
        return {
            'fight_id':fight_id,
            'err':fight_soup.find('h2').text #code will break if theres no h2 (doubtful though)
                } #find Server Too Busy error
    fight_details = get_fight_details(fight_soup)
    result_data = get_fight_result_data(fight_soup)
    total_fight_stats = fight_stats + ';' + fight_details + ';' + result_data
    final = {'fight_id':fight_id, 'err':None}
    final.update(dict(zip(FIGHT_HEADER.split(';'), total_fight_stats.split(';'))))
    return final

def get_fight_stats(fight_soup: BeautifulSoup) -> str:
	tables = fight_soup.findAll('tbody')
	total_fight_data = [tables[0],tables[2]] ##err
	fight_stats = []
	for table in total_fight_data:
	    row = table.find('tr')
	    stats = ''
	    for data in row.findAll('td'):
	        if stats == '':
	            stats = data.text
	        else:
	            stats = stats + ',' + data.text
	    fight_stats.append(stats.replace('  ', '').replace('\n\n', '')\
	    	.replace('\n', ',').replace(', ', ',').replace(' ,',','))
	fight_stats[1] = ';'.join(fight_stats[1].split(',')[6:])
	fight_stats[0] = ';'.join(fight_stats[0].split(','))
	fight_stats = ';'.join(fight_stats)
	return fight_stats

def get_fight_details(fight_soup: BeautifulSoup) -> str:
	columns = ''
	for div in fight_soup.findAll('div', {'class':'b-fight-details__content'}):
	    for col in div.findAll('p', {'class': 'b-fight-details__text'}):
	        if columns == '':
	            columns = col.text
	        else:
	            columns = columns + ',' +(col.text)

	columns = columns.replace('  ', '').replace('\n\n\n\n', ',')\
	.replace('\n', '').replace(', ', ',').replace(' ,',',')\
	.replace('Method: ', '').replace('Round:', '').replace('Time:', '')\
	.replace('Time format:', '').replace('Referee:', '')

	fight_details = ';'.join(columns.split(',')[:5])

	return fight_details

def get_fight_result_data(fight_soup: BeautifulSoup) -> str:
	winner = ''
	for div in fight_soup.findAll('div', {'class': 'b-fight-details__person'}):
	    if div.find('i', {'class':
	    	'b-fight-details__person-status b-fight-details__person-status_style_green'})!=None:
	        winner = div.find('h3', {'class':'b-fight-details__person-name'})\
	        .text.replace(' \n', '').replace('\n', '')
	fight_type = fight_soup.find("i",{"class":"b-fight-details__fight-title"})\
	.text.replace('  ', '').replace('\n', '')
	return fight_type + ';' + winner