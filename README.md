# Numbeo Analysis

The numbeo.com portal is a community platform that accumulates information on the cost of living: prices of products, rent, fees, etc.  The portal was a source of inspiration, to prepare a project that would aid the search for housing in different regions of Europe. 

The Numbeo Analysis  project was designed to build a simple database based on data from numbeo.com. The data was obtained by the web scraping method using python libraries.
Based on the collected data, a short data analysis was conducted to compare the cost of renting and buying an apartment in European cities, with Krakow as the reference point. 

The project consists of 3 notebooks: 
* `numbeo_scraper` used to download/refresh data from the numbeo.com platform, Data are stored in  `numbeo.json` file. 
* `numbeo_db` used to complete/update the numbeo_db database. The notebook is based on the data collected in the notebook `numbeo_scraper`. 
* `numbeo_analysis` used for data analysis.

## Instalation and running

1. To install the libraries necessary to run the project in the terminal, run the command: pipenv install
2. In order to launch the project: pipenv run jupyter notebook



