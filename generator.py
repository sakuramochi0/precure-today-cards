#!/usr/bin/env python3
# generator.py - make tweet and que from db_file
from datetime import date, timedelta
from collections import deque
import yaml
from today_cards import CHARACTER, TEXT

db_file = 'cards.yml'
que_file = 'ques.yml'
img_dir = 'img/'

def read_file(file):
    with open(file) as f:
        return yaml.load(f)

def tweet_generator(card_id, past, num):
    '''Generate tweet text from db.'''
    print('='*8)
    cards = read_file(db_file)
    card = cards[card_id]

    # name of the week
    if past == 0:
        week = '今週'
    elif past == 1:
        week = '先週'
    else:
        week = '{}週間前'.format(past)

    if 'comment' in card.keys() and card['comment']:
        status = '{0}の{1}枚目の画像は、{2}の{3}{desu}\n{4}「{5}」'.format(
            week, num, card['chara_name'], card['card_name'], card['comment_name'], card['comment'], desu=TEXT[CHARACTER]['desu'])
    else:
        status = '{0}の{1}枚目の画像は、{thiscard}{desu}'.format(week, num, thiscard=TEXT[CHARACTER]['thiscard'], desu=TEXT[CHARACTER]['desu'])

    if 'uploaded_img_url' in card.keys() and card['uploaded_img_url']:
        uploaded_img_url = cards[card_id]['uploaded_img_url']
        status += ' ' + uploaded_img_url
        return {'status': status}
    else:
        img_path = img_dir + card['filename']
        return {'status': status, 'img_path': img_path}
            
def make_que(mode='daily', past=0):
    '''
    Make tweet que according to mode (weekly/daily).
    If 'past' is given, return a list 'past' weeks ago.
    '''
    # read db and limit cards to in this week
    cards = read_file(db_file)
    dates = make_list_of_the_week(past)
    cards = list((id, v) for id, v in cards.items() if v['date'] in dates) # limit to cards in dates
    cards = sorted(cards, key=lambda x: x[1]['card_num']) # sort by card_num
    if mode == 'daily':
        num = len([card for card in cards if 'chara_name' in card[1].keys() and card[1]['chara_name'] != 'リボン' and card[1]['chara_name'] != 'ぐらさん'])
        print(num)
        cards = cards[:num] # character cards only
    
    # make que
    ques = deque([])
    num = 0
    for i, card in cards:
        num += 1
        card_id = '{}-{}-{}'.format(card['series'], card['series_num'], card['card_num'])
        que = (card_id, past, num)
        ques.append(que)

    # write que
    with open(que_file, 'w') as f:
        yaml.dump(ques, f)
    ques = read_file(que_file)
    print('make ques:', ques)

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
    print('dates:', dates)
    return dates
    
