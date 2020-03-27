import json
import os
import multiprocessing
import threading
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple

import scraper

FIGHTERS_PAGE_URL = 'http://ufcstats.com/statistics/fighters?char={letter}&page=all'
FIGHER_URL = 'http://ufcstats.com/fighter-details/{figher_id}'

def get_fighter_info(fighter_id:Dict(str)) -> Dict[str,str]:
	'''
	pass any dict that contains {'figher_id':'ee457ef1e1c326c1'}
	returns same dict with data appended 
	'''
	url = FIGHER_URL.format(fighter_id=fighter_id['fighter_id'])
	fighter_soup = scraper.make_soup(url)
	divs = fighter_soup.findAll('li', {'class':"b-list__box-list-item b-list__box-list-item_type_block"})
	data = []
	for i, div in enumerate(divs):
		if i == 5:
			break
		data.append(div.text.replace('  ', '').replace('\n', '').replace('Height:', '').replace('Weight:', '')\
					.replace('Reach:', '').replace('STANCE:', '').replace('DOB:', ''))
	header = ['Height', 'Weight', 'Reach', 'Stance', 'DOB']
	return data


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
					'figher_id' : name['href'].split('/')[-1],
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


