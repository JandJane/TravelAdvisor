# -*- coding: utf-8 -*-

import config
import utils
import _thread
import telebot
import time
import numpy as np
import math
from telegram.ext import CommandHandler, CallbackQueryHandler, Updater, MessageHandler, Filters

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']
bot = telebot.TeleBot(config.TOKEN)
queries = {}
waiting_for_origin_flag = False
waiting_for_destination_flag = False

class Query:
    def __init__(self, origin):
        try:
            self.origin = config.iata[origin]
        except KeyError:
            pass  # add better error handling
        self.destination = None
        self.adults = None
        self.stops = None
        self.stars = None
        self.flight = ''
        self.hotel = ''

    def set_destination(self, destination):
        try:
            self.destination = config.iata[destination]
        except KeyError:
            pass  # add better error handling

    def get_prices(self):
        print(self.origin)
        print(self.destination)
        t = time.time()
        date = time.gmtime(time.time())
        hotels = {}
        flights = {}
        # we will check prices for 1, 3 and 6 months ahead
        for i in [1, 3, 6]:
            # bringing date to YYYY-MM-DD format
            if date.tm_mon + i == 12:  #
                month = str(date.tm_year) + '-' + '12'
            elif date.tm_mon + i > 12:
                month = str(date.tm_year + 1) + '-' + '{:02d}'.format((date.tm_mon + i) % 12)
            else:
                month = str(date.tm_year) + '-' + '{:02d}'.format((date.tm_mon + i) % 12)
            # looking for flights for the 4th, 15th and 20th day of each month
            for j in [4, 15, 20]:
                depart_date = month + '-{:02d}'.format(j)
                return_date = month + '-{:02d}'.format(j + 7)  # trip length is set 7 night by default
                if j == 4:
                    flights['_'.join([str(i), '{:02d}'.format(j), 'with', 'stops'])] = None
                    flights['_'.join([str(i), '{:02d}'.format(j), 'without', 'stops'])] = None
                    _thread.start_new_thread(utils.find_flights, (self.origin, self.destination, depart_date,
                                                                  return_date, self.adults, self.stops, flights, i, j))
                hotels['_'.join([str(i), '{:02d}'.format(j)])] = None
                if self.stars != 2:  # suggest a lower-class alternative if possible
                    hotels['_'.join([str(i), '{:02d}'.format(j), 'lower', 'class'])] = None
                if self.stars != 5:  # suggest a higher-class alternative if possible
                    hotels['_'.join([str(i), '{:02d}'.format(j), 'higher', 'class'])] = None
                _thread.start_new_thread(utils.find_hotels, (self.destination, depart_date, return_date, self.adults,
                                                             self.stars, hotels, i, j))
        while (None in hotels.values() or None in flights.values()) and (time.time() - t < 180):
            time.sleep(10)
        print(time.time() - t)  # DEBUG
        return hotels, flights

    def handle(self):
        hotels, flights = self.get_prices()
        message = self.response_message(hotels, flights)
        return message

    def response_message(self, hotels, flights):
        date = time.gmtime(time.time())
        print(hotels)  # DEBUG
        print(flights)  # DEBUG
        msg = ''
        avg_alternative_flight = np.array([])
        avg_alternative_lower_class_hotel = np.array([])
        avg_alternative_higher_class_hotel = np.array([])
        for i in [1, 3, 6]:
            print(i, msg)
            if self.stops == 0:
                if flights['_'.join([str(i), '04', 'without', 'stops'])] and \
                                flights['_'.join([str(i), '04', 'without', 'stops'])] != 10 ** 9:
                    avg_flight = flights['_'.join([str(i), '04', 'without', 'stops'])]
                    if flights['_'.join([str(i), '04', 'with', 'stops'])] and \
                                    flights['_'.join([str(i), '04', 'with', 'stops'])] != 10 ** 9:
                        fraction = flights['_'.join([str(i), '04', 'with', 'stops'])] / \
                                flights['_'.join([str(i), '04', 'without', 'stops'])]
                        avg_alternative_flight = np.append(avg_alternative_flight, fraction)
            else:
                if flights['_'.join([str(i), '04', 'with', 'stops'])] and \
                                flights['_'.join([str(i), '04', 'with', 'stops'])] != 10 ** 9:
                    avg_flight = flights['_'.join([str(i), '04', 'with', 'stops'])]
                    if flights['_'.join([str(i), '04', 'without', 'stops'])] and \
                                    flights['_'.join([str(i), '04', 'without', 'stops'])] != 10 ** 9:
                        fraction = flights['_'.join([str(i), '04', 'without', 'stops'])] / \
                                   flights['_'.join([str(i), '04', 'with', 'stops'])]
                        avg_alternative_flight = np.append(avg_alternative_flight, fraction)
            print(avg_flight)  # DEBUG
            avg_hotel = np.array([])
            for j in [4, 15, 20]:
                print(j)
                if hotels['_'.join([str(i), '{:02d}'.format(j)])] and \
                                hotels['_'.join([str(i), '{:02d}'.format(j)])] != 10 ** 9:
                    avg_hotel = np.append(avg_hotel, hotels['_'.join([str(i), '{:02d}'.format(j)])])
                    print(avg_hotel)  # DEBUG
                    if self.stars != 2 and hotels['_'.join([str(i), '{:02d}'.format(j), 'lower', 'class'])] and \
                                    hotels['_'.join([str(i), '{:02d}'.format(j), 'lower', 'class'])] != 10 ** 9:
                        fraction = hotels['_'.join([str(i), '{:02d}'.format(j), 'lower', 'class'])] / \
                                    hotels['_'.join([str(i), '{:02d}'.format(j)])]
                        avg_alternative_lower_class_hotel = np.append(avg_alternative_lower_class_hotel, fraction)
                    if self.stars != 5 and hotels['_'.join([str(i), '{:02d}'.format(j), 'higher', 'class'])] and \
                                    hotels['_'.join([str(i), '{:02d}'.format(j), 'higher', 'class'])] != 10 ** 9:
                        fraction = hotels['_'.join([str(i), '{:02d}'.format(j), 'higher', 'class'])] / \
                                   hotels['_'.join([str(i), '{:02d}'.format(j)])]
                        avg_alternative_higher_class_hotel = np.append(avg_alternative_higher_class_hotel, fraction)
            try:
                msg += 'Trip in ' + MONTHS[(date.tm_mon + i - 1) % 12] + ' would cost you about ' + str((avg_flight
                                                                            + np.mean(avg_hotel)) // 60) + ' USD \n'
                msg += '(' + str(math.floor(avg_flight * 100 / (avg_flight + np.mean(avg_hotel)))) + '% - flight, '
                msg += str(
                    math.ceil(np.mean(avg_hotel) * 100 / (avg_flight + np.mean(avg_hotel)))) + '% - hotel). \n\n'
            except Exception as e:
                print(e)
        print(avg_alternative_flight)  # DEBUG
        print(avg_alternative_lower_class_hotel)  # DEBUG
        print(avg_alternative_higher_class_hotel)  # DEBUG
        if np.size(avg_alternative_flight) != 0:
            if self.stops == 0 and np.mean(avg_alternative_flight) <= 0.8:
                profit = math.ceil((1 - np.mean(avg_alternative_flight)) * 100)
                msg += 'A flight with a short change would be ' + str(profit) + '% cheaper.\n\n'
            elif self.stops != 0 and np.mean(avg_alternative_flight) <= 1.2:
                profit = math.floor((np.mean(avg_alternative_flight) - 1) * 100)
                msg += 'Flights without stops ' + str(profit) + '% more expensive.\n\n'
        if np.size(avg_alternative_higher_class_hotel) != 0:
            profit = math.floor((np.mean(avg_alternative_higher_class_hotel) - 1) * 100)
            msg += 'Hotel of a higher class is ' + str(profit) + '% more expensive.\n\n'
        if np.size(avg_alternative_lower_class_hotel) != 0:
            profit = math.ceil((1 - np.mean(avg_alternative_lower_class_hotel)) * 100)
            msg += 'Hotel of a lower class is ' + str(profit) + '% cheaper.\n\n'
        return msg


def handle_callback(bot, update):
    bot.answer_callback_query(update.callback_query.id)
    user = update.callback_query.message.chat.id
    data = update.callback_query.data
    time.sleep(0.2)
    if data[:4] == 'ppl_':
        queries[user].adults = int(data[4:])
        bot.send_message(user, config.stop_text,
                         reply_markup=utils.generate_keyboard(step='stop'))
    elif data[:4] == 'stop':
        queries[user].stops = int(data[4:])
        bot.send_message(user, config.strs_text,
                         reply_markup=utils.generate_keyboard(step='strs'))
    else:
        queries[user].stars = int(data[4:])
        bot.send_message(user, config.wait_text)
        bot.send_message(user, queries[user].handle())


def handle_start(bot, update):
    pass


def handle_query(bot, update):
    global waiting_for_origin_flag
    waiting_for_origin_flag = True
    bot.send_message(update.message.chat.id, config.orgn_text)


def handle_message(bot, update):
    global waiting_for_origin_flag, waiting_for_destination_flag
    user = update.message.chat.id
    text = update.message.text
    time.sleep(0.2)
    if waiting_for_origin_flag:
        queries[user] = Query(text.lower())
        waiting_for_origin_flag = False
        waiting_for_destination_flag = True
        bot.send_message(user, config.dstn_text)
    elif waiting_for_destination_flag:
        queries[user].set_destination(text.lower())
        waiting_for_destination_flag = False
        bot.send_message(chat_id=user, text=config.ppl_text, reply_markup=utils.generate_keyboard(step='ppl'))


updater = Updater(config.TOKEN)

updater.dispatcher.add_handler(CommandHandler('start', handle_start))
updater.dispatcher.add_handler(CommandHandler('query', handle_query))
updater.dispatcher.add_handler(CallbackQueryHandler(handle_callback))
updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))
updater.start_polling()
