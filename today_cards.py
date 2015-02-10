#!/usr/bin/env python3
import sys
import signal
import re
import time
import datetime
import yaml
from io import BytesIO
from collections import deque
from os import path
import requests
import subprocess
from apscheduler.scheduler import Scheduler
from bs4 import BeautifulSoup
from twython import Twython
from twython import TwythonError
from pymongo import Connection
from PIL import Image

URL_LIST = 'url-list.txt'

url_prefix = 'http://precure-live.com/allstars/'
page_url = url_prefix + 'precure-card/today-card.html'
headers = {'referer': url_prefix + 'index.html'}

que_file = 'ques.yaml'
cred_file = '.credentials'
last_date_file = 'last_date.txt'

CHARACTER = 'glassan'
TEXT = {'ribbon': {'update': '更新されましたわ！',
                   'thiscard': 'こちらのカード',
                   'desu': 'ですわ！'},
        'glassan':{'update': '更新されたぜ！',
                   'thiscard': 'このカード',
                   'desu': 'だぜ！'},
        }

que_file = 'ques.yaml'
cards = Connection().precure_dcd_today_card.cards

sched = Scheduler()
sched.start()

def auth():
    '''
    authonticated the account and return twitter class
    '''
    # read app credentials
    with open(cred_file) as f:
        app_key, app_secret, oauth_token, oauth_secret = [x.strip() for x in f]
    t = Twython(app_key, app_secret, oauth_token, oauth_secret)
    return t

def tweet(status='', img_path=None):
    '''tweet a status text'''
    t = auth()
    if img_path:
        img = open(img_path, 'rb')
        res = t.update_status_with_media(status=status, media=img)
    else:
        res =t.update_status(status=status)
    return res

def run(mode='daily'):
    '''Read ques, tweet a tweet, and write ques'''
    # read que_file
    with open(que_file) as q:
        ques = yaml.load(q)
    if len(ques) == 0:
        make_que(mode)
        with open(que_file) as q:
            ques = yaml.load(q)
        if len(ques) == 0: # on Thursday and yet get new cards
            make_que(mode, past=1)

    que = ques.popleft()

    # tweet
    status = tweet_generator(*que)
    res = tweet(**status)
    print('Remained ques:', ques)

    # update db
    id = que[0]
    img_url = res['entities']['media'][0]['url']
    cards.update({'_id': id}, {'$set': {'img_url_twitter': img_url}})

    # update que_file
    with open(que_file, 'w') as q:
        yaml.dump(ques, q, allow_unicode=True, default_flow_style=False)

def download():
    '''Try download cards until updated and set weekly tweet'''
    get_new_card = download_cards()
    if get_new_card:
        tweet('今日のカードが{update}'.format(update=TEXT[CHARACTER]['update']))
        make_que('weekly')  # set weekly tweet schedule
        now = datetime.datetime.now() + datetime.timedelta(minutes=10)
        for t in range(12):
            # run('weekly') 12 times every 5 minutes
            sched.add_date_job(run, now + datetime.timedelta(minutes=t), args=['weekly']) 
        sched.print_jobs()
        time.sleep(60 * 60) # sleep 1hour

def get_title(url):
    '''get the first part of the page title from the url'''
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text)
    title = soup.title.text.strip()
    match = re.search(r'(.+) - ', title)
    if match:
        title = match.group(1)
    else:
        print(title)
        match = re.search(r'(.+) : ', title)
        if match:
            title = match.group(1)
    return title

def get_img_alt(url):
    '''Get the alt text of the first img.'''
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text)
    texts = [img['alt'] for img in soup(id='column-right')[0]('img') if img['alt']]
    return texts[0]
    
def check_update():
    '''check DCD news and tweet the information'''
    url_base = 'http://precure-live.com'
    r = requests.get('http://precure-live.com/allstars/')
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text)

    # extract only new news items
    news = soup(id='precure-news')[0].span.find_parent().find_next_siblings()
    new_news = ''
    for i in news:
        if i.has_attr('class'):
            break
        new_news += str(i)
    news = BeautifulSoup(''.join(new_news))
    news = set(news('a', class_=re.compile(r'^news.*')))

    # date check
    with open(last_date_file) as f:
        last_date = f.read().strip()
    new_date = [i for i in soup.select('#precure-news dt') if i.span][0].next
    if new_date != last_date:
        for i in news:
            cls = i['class'][0]
            if cls == 'news-news':
                category = 'ニュース'
                if i.text == 'カードカタログ':
                    continue
            elif cls == 'news-event':
                category = 'イベント'
            elif cls == 'news-goods':
                category = 'グッズ'
            elif cls == 'news-cardlist':
                category = 'カードリスト'
            elif cls == 'news-about':
                category = 'あそびかた'
            else:
                continue # not hit known update category
            url = url_base + i.get('href')
            title = get_title(url)
            if category == 'ニュース':
                text = get_img_alt(url)
                if text:
                    title += ' ' + text
            print('「{category}」のページが{text_update} / {title} - {url}'.format(category=category, title=title, url=url, text_update=TEXT[CHARACTER]['update']))
            try:
                tweet('「{category}」のページが{text_update} / {title} - {url}'.format(category=category, title=title, url=url, text_update=TEXT[CHARACTER]['update']))
            except TwythonError as e:
                print(e)

        with open(last_date_file, 'w') as f:
            f.write(new_date)

def tweet_generator(id, past, num):
    '''Generate tweet text from db.'''
    print('-' * 8)
    card = cards.find({'_id': id})

    # name of the week
    if past == 0:
        week = '今週'
    elif past == 1:
        week = '先週'
    else:
        week = '{}週間前'.format(past)

    if 'comment' in card.keys() and card['comment']:
        status = '{0}の{1}枚目の画像は、{2}の{3}{desu}\n{4}「{5}」'.format(
            week,
            num,
            card['chara_name'],
            card['card_name'],
            card['comment_name'],
            card['comment'],
            desu=TEXT[CHARACTER]['desu']
        )
    else:
        status = '{0}の{1}枚目の画像は、{thiscard}{desu}'.format(
            week,
            num,
            thiscard=TEXT[CHARACTER]['thiscard'],
            desu=TEXT[CHARACTER]['desu']
        )

    if card['img_url_twitter']:
        status += ' ' + card['img_url_twitter']
        return {'status': status}

    else:
        img_path = 'img/' + card['filename']
        return {'status': status, 'img_path': img_path}
            
def make_que(mode='daily', past=0):
    '''
    Make tweet que according to mode (weekly/daily).
    If 'past' is given, return a list 'past' weeks ago.
    '''
    # read db and limit cards to in this week
    a_week_ago = datetime.datetime.now() - datetime.timedelta(7)
    cards_in_week = cards.find({'date': {'$gt': a_week_ago}, 'chara': {'$ne': ''}}).sort('_id')

    if not cards:
        return
    elif mode == 'daily':
        # もし、データが未入力らしければ
        if not cards_in_week.count():
            cards_in_week = cards.find({'date': {'$gt': a_week_ago}}).sort('_id').limit(4)
    
    # make que
    ques = deque([])
    for i, card in enumerate(cards_in_week, 1):
        que = (card['id'], past, i)
        ques.append(que)

    # write que
    with open(que_file, 'w') as f:
        yaml.dump(ques, f)

def generate_url_list():
    urls = sorted(cards.find().distinct('img_url'))
    with open(URL_LIST, 'w') as f:
        f.write('\n'.join(urls))
    # update repo
    subprocess.call(['git', 'add', URL_LIST])
    subprocess.call(['git', 'commit', '-m', 'Update'])
    subprocess.call(['git', 'push'])

def download_cards():
    '''download all card image of the week'''
    max_card_num = 13
    downloaded_list = []        # appended downloaded card_num
    retry = 0

    exist_filenames = cares

    # download all the card
    while len(downloaded_list) < max_card_num:
        retry += 1
        if retry > 300:
            print('- over 300 retry, exit')
            break
            
        # get html
        r = requests.get(page_url, headers=headers)

        # parse html & get img_url
        regex = re.compile(r'image/precure-card/[^/]+/([^/]+)/([^"]+)')
        match = re.search(regex, r.text)
        update_num = match.group(1)
        img_url = url_prefix + match.group()
        filename = match.group(2)

        # cf. filename: 'img_card_happiness01-68_e8d7824dxjm3.jpg'
        regex = re.compile(r'img_card_(.+)(\d{2,})-(\d{2,})_(.+).jpg')
        match = re.search(regex, filename)
        series = match.group(1)
        series_num = int(match.group(2))
        card_num = int(match.group(3))
        id = '{}-{}-{}'.format(series, series_num, card_num)
        date = datetime.date.today()

        # prevent duplicated download
        if cards.find({'filename': filename}).count():
            return False # not get new cards
        
        # check if the card is new or not
        if not card_num in downloaded_list:
            print('- get a new card #', len(downloaded_list) + 1)
            # get img
            r = requests.get(img_url, headers=headers)
            with open('img/jpg/' + filename, 'wb') as f:
                f.write(r.content)
            print('- save jpeg image:', filename)

            # convert to png image
            img = Image.open(BytesIO(r_img.content))
            img.save('img/' + path.splitext(filename)[0] + 'png')
            
            downloaded_list.append(card_num)
            print('- add downloaded_list:', id)

            new_card = {
                '_id': id,
                'date': date,
                'series': series,
                'series_num': series_num,
                'card_num': card_num,
                'filename': filename,
                'img_url': img_url,
                'update_num': update_num,
                # placeholders
                'chara': '',
                'coode': '',
                'comment_chara': '',
                'comment': '',
            }            
            cards.update({'_id': id}, {'$set': new_card}, upsert=True)

            print('Append a record to the database:', id)
            print('-' * 8)
                            
        # safe access
        time.sleep(1)

    generate_url_list()

    return True  # get new cards

def redownload():
    '''re-download all the images'''
    for card in cards.find():
        img_url = card['img_url']
        filename = card['filename']
        r = requests.get(img_url, headers=headers)
        with open('img/' + filename, 'wb') as f:
            f.write(r.content)
        print('Write image:', filename)

if __name__ == '__main__':
    
    weekly = False
    args = sys.argv[1:]

    if args[0] == 'weekly':
        weekly = True
        args.pop(0)

    if args[0] == 'tweet':
        tweet(status=args[1:])
        if args[1] == 'img':
            tweet(status=args[2:],img_path=args[1])
    elif args[0] == 'make_que':
        mode = 'daily'
        past = 0
        if len(args) > 2:
            past = int(args[2])
        if len(args) > 1:
            if args[1] == 'weekly':
                mode = 'weekly'
            elif args[1] == 'daily':
                mode = 'daily'
        generator.make_que(mode, past)
    elif args[0] == 'download':
        download()
    elif args[0] == 'check_update':
        check_update()
    elif args[0] == 'run':
        run()
