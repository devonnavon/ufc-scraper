# UFC data scraper
- Scrapes event, fight, and fighter data from [UFC Stats](http://ufcstats.com/statistics/events/completed)
- Scrape data stored in data folder (for now), will check against events to scrape only new data

## Project Structure
```
ufc-scraper
│   readme.md
│   requirements.txt
│   run_scraper.py    
│   cleaning.ipynb -initial cleaning and feature engineering, will change into .py when MVP done   
│
└───data
│   │   events.json
│   │   fights.json
│   │   fighters.json
│
└───scraper
│   │   init.py - general helper functions 
│   │   events.py 
│   │   fights.py
│   │   fighters.py
```

## To Run Scraper
```console
~$ python run_scraper.py
```
- The above should be update all files in the data folder
- If no data folder exists it will create one
- If it is updating it will load only new events and new fights
- Will always reload all fighter data (takes abotu 35 min) unless there is nothing to update

