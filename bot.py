import config
import utils
import _thread
import telebot
import time
import numpy as np
import math
from telegram.ext import CommandHandler, CallbackQueryHandler, Updater, MessageHandler, Filters

bot = telebot.TeleBot(config.TOKEN)
queries = {}
waiting_for_origin = False
waiting_for_destination = False

class Query:
    def __init__(self, origin):
        self.origin = origin
        self.destination = None
        self.adults = None
        self.stops = None
        self.stars = None
        self.flight = ''
        self.hotel = ''

    def generate_text(self):
        t = time.time()
        date = time.gmtime(time.time())
        msg = ''
        hotels = {}
        flights = {}
        for i in [1, 3, 6]:
            if date.tm_mon + i == 12:
                month = str(date.tm_year) + '-' + '12'
            elif date.tm_mon + i > 12:
                month = str(date.tm_year + 1) + '-' + '{:02d}'.format((date.tm_mon + i) % 12)
            else:
                month = str(date.tm_year) + '-' + '{:02d}'.format((date.tm_mon + i) % 12)
            for j in [4, 15, 20]:
                depart_date = month + '-{:02d}'.format(j)
                return_date = month + '-{:02d}'.format(j + 7)
                if j == 4:
                    flights['_'.join([str(i), '{:02d}'.format(j), 'with', 'stops'])] = None
                    flights['_'.join([str(i), '{:02d}'.format(j), 'without', 'stops'])] = None
                    _thread.start_new_thread(utils.find_flights, (config.iata[self.origin], config.iata[self.destination], \
                                                                    depart_date, return_date, self.adults, self.stops, \
                                                                    flights, i, j))
                hotels['_'.join([str(i), '{:02d}'.format(j)])] = None
                if self.stars != 2:
                    hotels['_'.join([str(i), '{:02d}'.format(j), 'lower', 'class'])] = None
                if self.stars != 5:
                    hotels['_'.join([str(i), '{:02d}'.format(j), 'higher', 'class'])] = None
                _thread.start_new_thread(utils.find_hotels, (config.iata[self.destination], depart_date, return_date, \
                                                             self.adults, self.stars, hotels, i, j))
        while None in hotels.values() or None in flights.values():
            time.sleep(10)
        print(hotels)
        print(flights)
        for i in [1, 3, 6]:
            print(msg)
            print(i)
            if self.stops == 0:
                if flights['_'.join([str(i), '04', 'without', 'stops'])] and \
                                flights['_'.join([str(i), '04', 'without', 'stops'])] != 10**9:
                    avg_flight = flights['_'.join([str(i), '04', 'without', 'stops'])]
                else:
                    print('_'.join([str(i), '04', 'without', 'stops']))
                    print(bool(flights['_'.join([str(i), '04', 'without', 'stops'])]))
                    print(flights['_'.join([str(i), '04', 'without', 'stops'])] != 10**9)
                    continue
            else:
                if flights['_'.join([str(i), '04', 'with', 'stops'])] and \
                                flights['_'.join([str(i), '04', 'with', 'stops'])] != 10**9:
                    avg_flight = flights['_'.join([str(i), '04', 'with', 'stops'])]
                else:
                    print('_'.join([str(i), '04', 'with', 'stops']))
                    print(bool(flights['_'.join([str(i), '04', 'with', 'stops'])]))
                    print(flights['_'.join([str(i), '04', 'with', 'stops'])])
                    continue
            avg_hotel = np.array([])
            for j in [4, 15, 20]:
                print(j)
                if hotels['_'.join([str(i), '{:02d}'.format(j)])] and \
                                hotels['_'.join([str(i), '{:02d}'.format(j)])] != 10**9:
                    avg_hotel = np.append(avg_hotel, hotels['_'.join([str(i), '{:02d}'.format(j)])])
                else:
                    print('_'.join([str(i), '{:02d}'.format(j)]))
                    print(bool(hotels['_'.join([str(i), '{:02d}'.format(j)])]))
                    print(hotels['_'.join([str(i), '{:02d}'.format(j)])])
                    continue
            if np.size(avg_hotel) != 0:
                msg += '\n Поездка в ..месяце.. обойдётся примерно в ' + str(avg_flight + np.mean(avg_hotel)) + ' Р \n'
                msg += '(' + str(math.floor(avg_flight * 100 / (avg_flight + np.mean(avg_hotel)))) + '% - перелёт, '
                msg += str(math.ceil(np.mean(avg_hotel) * 100 / (avg_flight + np.mean(avg_hotel)))) + '% - проживание). \n'
        print(time.time()-t)
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
        bot.send_message(user, queries[user].generate_text())


def handle_start(bot, update):
    pass


def handle_query(bot, update):
    global waiting_for_origin
    waiting_for_origin = True
    bot.send_message(update.message.chat.id, config.orgn_text)


def handle_message(bot, update):
    global waiting_for_origin, waiting_for_destination
    user = update.message.chat.id
    text = update.message.text
    time.sleep(0.2)
    if waiting_for_origin:
        queries[user] = Query(text.lower())
        waiting_for_origin = False
        waiting_for_destination = True
        bot.send_message(user, config.dstn_text)
    elif waiting_for_destination:
        queries[user].destination = text.lower()
        waiting_for_destination = False
        bot.send_message(chat_id=user, text=config.ppl_text, reply_markup=utils.generate_keyboard(step='ppl'))


updater = Updater(config.TOKEN)

updater.dispatcher.add_handler(CommandHandler('start', handle_start))
updater.dispatcher.add_handler(CommandHandler('query', handle_query))
updater.dispatcher.add_handler(CallbackQueryHandler(handle_callback))
updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))
updater.start_polling()

