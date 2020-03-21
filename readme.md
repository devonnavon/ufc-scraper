# UFC data scraper
- Scrapes event, fight, and fighter data from [UFC Stats](http://ufcstats.com/statistics/events/completed)
- Scrape data stored in data folder (for now), will check against events to scrape only new data

## Project Structure
```
ufc-scraper
│   readme.md
│   requirements.txt
│   run_scraper.py    
│   run_scraper.ipynb -where I'm building it     
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


