# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import urllib.request
import urllib.parse
import lxml.html as html
import _thread
import time
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

dcap = dict(webdriver.common.desired_capabilities.DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0")

def capture_stop_duration(text):
    text = list(text.split('\n'))
    if len(text) < 2:
        return 0
    else:
        if text[1][-1] == 'ч':
            return int(text[1][10:-1])
        else:
            text = list(text[1][10:-1].split('ч '))
            if len(text) == 1:
                return 1
            else:
                return int(text[0]) + 1


def find_flights(origin, destination, depart_date, return_date, adults, stops, flights, i, j):
    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true', '--ssl-protocol=tlsv1'], desired_capabilities=dcap)
    driver.set_window_size(1024, 80)
    data = {'origin': origin, 'destination': destination, 'depart_date': depart_date, 'return_date': return_date, 'adults': adults, 'trip_class': '0', 'with_request': 'true'}
    enc_data = urllib.parse.urlencode(data)
    url = "https://search.aviasales.ru/" + "?" + enc_data
    driver.get(url)
    time.sleep(30)
    prices = np.array([])
    #wait until expected cond
    if not driver.find_elements_by_css_selector('.filters__item.filter.\--baggage.is-hidden'):
        driver.find_elements_by_class_name('checkboxes-list__item')[1].find_element_by_class_name(
            'checkboxes-list__extra-uncheck-other').click()
    else:
        driver.find_elements_by_class_name('checkboxes-list__item')[0].find_element_by_class_name(
            'checkboxes-list__extra-uncheck-other').click()
    try:
        for flight in driver.find_element_by_class_name('product-list').find_elements_by_class_name('buy-button__link'):
            prices = np.append(prices,
                               int(flight.find_element_by_css_selector('.price.\--rub').text.replace('\u2009', '')))
    except Exception:
        pass

    if prices.size != 0:
        flights[str(i) + '_' + '{:02d}'.format(j) + '_without_stops'] = int(np.median(prices))
    else:
        flights[str(i) + '_' + '{:02d}'.format(j) + '_without_stops'] = 10 ** 9

    prices = np.array([])
    stops = max(stops, 3)
    if not driver.find_elements_by_css_selector('.filters__item.filter.\--baggage.is-hidden'):
        driver.find_elements_by_class_name('checkboxes-list__item')[2].find_element_by_class_name(
            'checkboxes-list__extra-uncheck-other').click()
    else:
        driver.find_elements_by_class_name('checkboxes-list__item')[1].find_element_by_class_name(
            'checkboxes-list__extra-uncheck-other').click()
    k = 0
    while k <= 2 and prices.size == 0:
        for flight in driver.find_element_by_class_name('product-list').find_elements_by_css_selector(
                '.ticket.product-list__ticket.\--openable'):
            onway_stops = flight.find_elements_by_css_selector('.segment-route__path-stop.\--plane.\--stop')
            for stop in onway_stops:
                stop.click()
            time.sleep(0.1)
            if any(map(lambda x: capture_stop_duration(x.text) > stops * 1.1, onway_stops)):
                continue
            prices = np.append(prices,
                               int(flight.find_element_by_class_name('buy-button__link').find_element_by_css_selector(
                                   '.price.\--rub').text.replace('\u2009', '')))
        if driver.find_element_by_class_name('show-more-products__button'):
            driver.find_element_by_class_name('show-more-products__button').click()
            k += 1
        else:
            k = 3
    if prices.size != 0:
        flights[str(i) + '_' + '{:02d}'.format(j) + '_with_stops'] = int(np.median(prices))
    else:
        flights[str(i) + '_' + '{:02d}'.format(j) + '_with_stops'] = 10**9

    driver.close()


def find_hotels(destination, checkIn, checkOut, adults, stars, hotels, i, j):
    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true', '--ssl-protocol=tlsv1'], desired_capabilities=dcap)
    data = {'checkIn': checkIn, 'checkOut': checkOut, 'destination': destination, 'adults': adults, 'language': 'ru-RU', 'currency': 'RUB'}
    enc_data = urllib.parse.urlencode(data)
    url = "https://search.hotellook.com/" + "?" + enc_data + '#f%5Bstars%5D=' + str(stars)
    driver.get(url)
    driver.set_window_size(1024, 800)
    time.sleep(30)
    if driver.find_elements_by_class_name('search-results-cards-wrapper-card'):
        prices = np.array([])
        for card in driver.find_elements_by_class_name('search-results-cards-wrapper-card'):
            try:
                prices = np.append(prices, int(card.find_element_by_class_name('main_gate-price').text[2:].replace(' ', '')))
            except Exception:
                pass
        if prices.size != 0:
            hotels[str(i) + '_' + '{:02d}'.format(j)] = int(np.median(prices))
            hotels[str(i) + '_' + '{:02d}'.format(j) + '_lower_class'] = 10 ** 9
            hotels[str(i) + '_' + '{:02d}'.format(j) + '_higher_class'] = 10 ** 9
        else:
            driver.save_screenshot('1.png')
            hotels[str(i) + '_' + '{:02d}'.format(j)] = 10 ** 9
            hotels[str(i) + '_' + '{:02d}'.format(j) + '_lower_class'] = 10 ** 9
            hotels[str(i) + '_' + '{:02d}'.format(j) + '_higher_class'] = 10 ** 9
    else:
        driver.find_element_by_class_name('filter-list').find_elements_by_tag_name('li')[1].find_element_by_tag_name(
            'a').click()
        for temp in [stars - 1, stars, stars + 1]:
            if 2 <= temp <= 5:
                prices = np.array([])
                driver.find_elements_by_class_name('hl-ui-checkboxes-item-input')[temp - 1].click()
                time.sleep(1)
                for card in driver.find_elements_by_class_name('hotels-grid-item_visible'):
                    prices = np.append(prices, int(card.find_element_by_class_name('hotels-grid-prices-best-value').find_element_by_class_name('hl-price-value').text.replace(' ', '')))
                if prices.size != 0:
                    hotels[str(i) + '_' + '{:02d}'.format(j) + (stars == temp + 1) * '_lower_class' + \
                           (stars == temp - 1) * '_higher_class'] = int(np.median(prices))
                else:
                    driver.save_screenshot('2.png')
                    hotels[str(i) + '_' + '{:02d}'.format(j) + (stars == temp + 1) * '_lower_class' + \
                           (stars == temp - 1) * '_higher_class'] = 10 ** 9
                driver.find_elements_by_class_name('hl-ui-checkboxes-item-input')[temp - 1].click()
                #driver.find_element_by_class_name('filter-list').find_elements_by_tag_name('li')[1].find_element_by_tag_name('a').click()
    driver.close()



def generate_keyboard(step):
    if step == 'ppl':
        keyboard = InlineKeyboardMarkup([], row_width=3)
        for i in range(1, 10):
            button = InlineKeyboardButton(text=str(i), callback_data='ppl_' + str(i))
            keyboard.inline_keyboard.append([button])
        return keyboard
    elif step == 'stop':
        keyboard = InlineKeyboardMarkup([])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text='No stops', callback_data='stop0')])
        for i in range(3, 12, 3):
            button = InlineKeyboardButton(text=str(i) + ' hrs', callback_data='stop' + str (i))
            keyboard.inline_keyboard.append([button])
        return keyboard
    else:
        keyboard = InlineKeyboardMarkup([], row_width=2)
        for i in range(2, 6):
            button = InlineKeyboardButton(text=str(i) + '*', callback_data='strs' + str(i))
            keyboard.inline_keyboard.append([button])
        return keyboard
