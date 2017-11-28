# -*- coding: utf-8 -*-
import lxml.html as html
import urllib.request
import csv
from lxml import etree

FILENAME = 'iata.csv'
url = 'http://g-avia.ru/kody_gorodov_vseh_stran_'
my_dict = {}
content = urllib.request.urlopen(url).read()
doc = html.fromstring(content)
table = etree.HTML(html.tostring(doc.find_class('table1')[0]))
cities = table.getchildren()[0].getchildren()[0].getchildren()[0].getchildren()
for i in range(1, len(cities)):
    fields = cities[i].getchildren()
    if fields[5].text != ' ':
        iata = fields[5].text
        if fields[1].text != ' ':
            my_dict[fields[1].text] = iata
        if fields[2].text != ' ':
            my_dict[fields[2].text] = iata
print(my_dict)
with open(FILENAME, 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['city', 'IATA'])
    writer.writeheader()
    for city in my_dict:
        writer.writerow({'city': city, 'IATA': my_dict[city]})
file.close()


