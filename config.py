# -*- coding: utf-8 -*-

import csv

TOKEN = _YOUR_TOKEN_
FILENAME = 'data/iata.csv'

orgn_text = 'Where would you like to start your trip?'
dstn_text = 'Where would you like to go?'
ppl_text = 'How many people are going'
stop_text = 'Are you ok with stops during the flight? If yes, choose maximum duration of a stop'
strs_text = 'Please, choose the category of hotel you would like to stay at'
wait_text = 'We are now handling your query:)\nIt may take up to 3 minutes.'
iata ={}

with open(FILENAME, 'r', newline='') as file:  # forming current users database from the file
    reader = csv.DictReader(file)
    for row in reader:
        iata[row['city'].lower()] = row['IATA']
    file.close()
