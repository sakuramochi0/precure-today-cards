#!/usr/bin/env python3
# generator.py - make tweet text from cards.csv
import pandas as pd
from datetime import date, timedelta
from collections import deque
import pickle

db_file = 'cards.csv'
que_file = 'ques.p'
img_dir = 'img/'

def tweet_generator(series, series_num, card_num, past, num):
    '''Generate tweet text from db.'''
    print('='*8)
    print('args',(series, series_num, card_num, past, num))
    cards = pd.read_csv(db_file)
    card = cards[(cards['series'] == series) & (cards['series_num'] == series_num) &
                 (cards['card_num'] == card_num)]
    # name of the week
    if past == 0:
        week = '今週'
    elif past == 1:
        week = '先週'
    else:
        week = '{}週間前'.format(past)

    comment = card['comment'].item()
    if str(comment) != '0':
        status = '{0}の{1}枚目の画像は、{2}の{3}ですわ！ {4}「{5}」'.format(
            week, num,
            card['chara_name'].item(), card['card_name'].item(),
            card['comment_name'].item(), card['comment'].item())
    else:
        status = '{0}の{1}枚目の画像は、こちらのカードですわ！'.format(week, num)

    uploaded_img_url = card['uploaded_img_url'].item()
    if str(uploaded_img_url) != '0' :
        status += ' ' + uploaded_img_url
        return {'status': status}
    else:
        img_path = img_dir + card['filename'].item()
        return {'status': status, 'img_path': img_path}
            
def make_que(mode='daily', past=0):
    '''Make tweet que accorfing to mode (weekly/daily).
    If 'past' is given, return a list 'past' weeks ago.'''
    ques = deque([])

    # read db and limit cards of this week
    cards = pd.read_csv(db_file)
    dates = make_list_of_the_week(past)
    cards = cards.query('date in dates')
    cards = cards.sort(['series', 'series_num', 'card_num'])
    if mode == 'daily':
        cards = cards[:4] # character cards only
    
    # make que
    num = 0
    for i, card in cards.iterrows():
        num += 1
        que = (card['series'], card['series_num'], card['card_num'], past, num)
        ques.append(que)

    # pickle que
    with open(que_file, 'wb') as f:
        pickle.dump(ques, f)

def make_list_of_the_week(past=0):
    '''Make a list of the days from the last Thursday to the next Wednesday.'''
    day = date.today()
    delta = 3 - day.weekday()  # 3 = thusday
    if delta > 0:
        delta -= 7
    last_thursday = day + timedelta(delta)
    if past > 0:
        last_thursday -= timedelta(past * 7)
    dates = [str(last_thursday + timedelta(x)) for x in range(7)]
    return dates
    
