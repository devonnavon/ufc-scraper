import json
import os
import multiprocessing
import threading
import itertools
from dateutil import parser
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple

import scraper

BASE_PATH = Path(os.getcwd())/'data'
FIGHTERS_PATH = BASE_PATH/'fighters.json'

FIGHTERS_PAGE_URL = 'http://ufcstats.com/statistics/fighters?char={letter}&page=all'
FIGHTER_URL = 'http://ufcstats.com/fighter-details/{fighter_id}'

def load_fighters():
	'''
	loads all fighters into data/fighters.json
	'''
	page_urls = get_fighter_page_urls() 
	fighter_ids_names = get_all_fighter_ids(page_urls) 
	
	final = []
	bs = 20 #batch size
	prev = 0 #starting index
	indices = range(bs,len(fighter_ids_names)+bs)

	print('Scraping all fight data: ')
	scraper.print_progress(0, len(fighter_ids_names), prefix = 'Progress:', suffix = 'Complete')

	for num in itertools.islice(indices,None,None,bs):
		final += get_all_fighter_info(fighter_ids_names[prev:num]) #run for batch
		prev = num
		if num > len(fighter_ids_names):
			num = len(fighter_ids_names) #dumb check for progress bar
		scraper.print_progress(num, len(fighter_ids_names), prefix = 'Progress:', suffix = 'Complete')
	
	with open(FIGHTERS_PATH, 'w') as f:
		f.write(json.dumps(final, indent=4, default=str))


def get_all_fighter_info(fighter_ids:List[Dict[str,str]]) -> List[Dict[str,str]]:
	'''
	get fighter info from a list of dicts fighters multithreads (should really generalize)
	'''
	q = multiprocessing.Queue() #queue to store the results
	t = {} #dict to hold our threads
	all_fighter_info = []

	def put_fighter_info(fighter_id):
		fighter_info = get_fighter_info(fighter_id)
		q.put(fighter_info)

	for fighter_id in fighter_ids:
		t[fighter_id['fighter_id']] = threading.Thread(target=put_fighter_info, args=(fighter_id,))
		t[fighter_id['fighter_id']].start()

	for thread in t: #join closes out the threads (i think)
		t[thread].join() 

	while not q.empty():
		queue_top = q.get()
		all_fighter_info.append(queue_top)

	retry=[]
	final=[]
	for info in all_fighter_info:
		if len(info) == 2: #nothing got appended
			retry.append(info)
		else:
			final.append(info)
	
	if len(retry) > 0:
		final+=get_all_fighter_info(retry)

	return final


def get_fighter_info(fighter_id:Dict[str,str]) -> Dict[str,str]:
	'''
	pass any dict that contains {'fighter_id':'ee457ef1e1c326c1'}
	returns same dict with data appended 
	'''
	url = FIGHTER_URL.format(fighter_id=fighter_id['fighter_id'])
	fighter_soup = scraper.make_soup(url)
	if fighter_soup.find('h2').text == 'Server Too Busy':
		return fighter_id
	divs = fighter_soup.findAll('li', {'class':"b-list__box-list-item b-list__box-list-item_type_block"})
	data = []
	for i, div in enumerate(divs):
		if i == 5:
			break
		data.append(div.text.replace('  ', '').replace('\n', '').replace('Height:', '').replace('Weight:', '')\
					.replace('Reach:', '').replace('STANCE:', '').replace('DOB:', ''))
	header = ['height', 'weight', 'reach', 'stance', 'dob']
	final = fighter_id.copy()
	final.update(dict(zip(header,data)))
	return final

def get_all_fighter_ids(page_urls:List[str]) -> List[Dict[str,str]]:
	'''
	get names and ids of all fighters multithreads (should really generalize)
	'''
	q = multiprocessing.Queue() #queue to store the results
	t = {} #dict to hold our threads
	all_fighter_ids = {}

	def put_fighter_ids(url):
		fighter_ids = get_fighter_ids(url)
		q.put({url:fighter_ids})

	for url in page_urls:
		t[url] = threading.Thread(target=put_fighter_ids, args=(url,))
		t[url].start()

	for thread in t: #join closes out the threads (i think)
		t[thread].join() 

	while not q.empty():
		queue_top = q.get()
		all_fighter_ids.update(queue_top)

	retry=[]
	final=[]
	for url in all_fighter_ids:
		if all_fighter_ids[url] is None:
			retry.append(url)
		else:
			final+=all_fighter_ids[url]
	
	if len(retry) > 0:
		final+=get_all_fighter_ids(retry)

	return final

def get_fighter_ids(page_url:str) -> List[Dict[str,str]]:
	'''
	for a fighter page get name and fighter_id
	'''
	fighter_ids = []
	fighter_name = ''

	soup = scraper.make_soup(page_url)
	if soup.find('h2').text == 'Server Too Busy':
		return None
	table = soup.find('tbody')
	names = table.findAll('a', {'class': 'b-link b-link_style_black'}, href=True)
	for i, name in enumerate(names):
		if (i+1)%3 != 0:
			if fighter_name == '':
				fighter_name = name.text
			else:
				fighter_name = fighter_name + ' ' + name.text
		else:
			fighter_ids.append(
				{
					'fighter_id' : name['href'].split('/')[-1],
					'fighter_name' : fighter_name
				}
			)
			fighter_name = ''
	return fighter_ids

def get_fighter_page_urls() -> List[str]:
	'''
	get all urls for every fighter page (pages based on last name)
	'''
	letters = [chr(i) for i in range(ord('a'),ord('a')+26)]
	page_urls = [FIGHTERS_PAGE_URL.format(letter=letter) for letter in letters]
	return page_urls


