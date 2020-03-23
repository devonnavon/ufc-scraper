import json
import os
from pathlib import Path
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple

import scraper

BASE_PATH = Path(os.getcwd())/'data'
EVENT_URL = 'http://ufcstats.com/event-details/{event_id}'
FIGHT_URL = 'http://ufcstats.com/fight-details/{fight_id}'

FIGHT_HEADER = '''r_fighter;b_fighter;r_kd;b_kd;r_sig_str.;b_sig_str.;r_sig_str_pct;b_sig_str_pct;
r_total_str.;b_total_str.;r_td;b_td;r_td_pct;b_td_pct;r_sub_att;b_sub_att;r_pass;b_pass;r_rev;b_rev;
r_head;b_head;r_body;b_body;r_leg;b_leg;r_distance;b_distance;r_clinch;b_clinch;r_ground;b_ground;
win_by;last_round;last_round_time;format;referee;fight_type;winner'''

def get_fight_ids(event_id:str) -> Dict[str,List[str]]:
    '''
    from list of event_ids returns dict with {event_id:[fight_id, fight_id,...]}
    '''
    soup = scraper.make_soup(EVENT_URL.format(event_id=event_id))
    fight_ids = []
    for row in soup.findAll('tr',{'class':'b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click'}):
        fight_ids.append(row.get('data-link').split('/')[-1])
    return {event_id:fight_ids}

def get_fight_info(fight_id:str) -> Dict[str,str]:
    fight_soup = scraper.make_soup(FIGHT_URL.format(fight_id=fight_id))
    fight_stats = get_fight_stats(fight_soup)
    fight_details = get_fight_details(fight_soup)
    result_data = get_fight_result_data(fight_soup)
    total_fight_stats = fight_stats + ';' + fight_details + ';' + result_data
    final = {'fight_id':fight_id}
    return final.update(dict(zip(FIGHT_HEADER.split(';'), total_fight_stats.split(';'))))

def get_fight_stats(fight_soup: BeautifulSoup) -> str:
	tables = fight_soup.findAll('tbody')
	total_fight_data = [tables[0],tables[2]]
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