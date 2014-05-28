#!/usr/bin/env python3
import sys
import signal
import yaml
import re
import subprocess
from os.path import basename
from datetime import datetime, timedelta
from apscheduler.scheduler import Scheduler
import requests
from bs4 import BeautifulSoup
from twython import Twython
from img_downloader import download_cards
import generator

db_file = 'cards.yaml'
que_file = 'ques.yaml'
cred_file = '.credentials'
last_news_file = 'last_news.txt'

sched = Scheduler()
sched.start()

def auth():
    '''
    authonticated the account and return twitter class
    '''
    # read app credentials
    with open(cred_file) as f:
        app_key, app_secret, oauth_token, oauth_secret = \
                            [x.strip() for x in f]
    t = Twython(app_key, app_secret, oauth_token, oauth_secret)
    return t

def get_timeline(user_id='precure_cards'):
    '''
    get twitter home timeline of the specific user
    '''
    t = auth()
    print('user_id: ', user_id)
    timeline = t.statuses.user_timeline(id=user_id)

    for line in timeline[:5]:
        print('{0[created_at]} {0[user][name]}({0[user][screen_name]}) {0[text]}'.format(line))

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
        generator.make_que(mode)
        with open(que_file) as q:
            ques = yaml.load(q)
        if len(ques) == 0: # on Thursday and yet get new cards
            generator.make_que(mode, past=1)

    que = ques.popleft()

    # tweet
    status = generator.tweet_generator(*que)
    res = tweet(**status)
    with open(db_file) as f:
        cards = yaml.load(f)
    print('Tweet this card:', cards[que[0]])
    print('Remained ques:', ques)

    # update db
    card_id = que[0]
    try:
        with open(db_file) as db:
            cards = yaml.load(db)
        cards[card_id]['uploaded_img_url'] = res['entities']['media'][0]['url']
    except:
        pass
    with open(db_file, 'w') as db:
        yaml.dump(cards, db)

    # update que_file
    with open(que_file, 'w') as q:
        yaml.dump(ques, q)

def download():
    '''Try download cards until updated and set weekly tweet'''
    get_new_card = download_cards()
    if get_new_card:
        tweet('今日のカードが更新されましたわ！')
        generator.make_que('weekly')  # set weekly tweet schedule
        now = datetime.now() + timedelta(seconds=10)
        for t in range(12):
            # run('weekly') 12 times every 5 minutes
            sched.add_date_job(run, now + timedelta(minutes=t), args=['weekly']) 
        sched.print_jobs()
        subprocess.call(['./input_description.py'])
        signal.pause()  # not to let program exit

def clear_uploaded_img_url():
    '''Clear img_url to re-upload image files.'''
    with open(db_file) as db:
        cards = yaml.load(db)
    for card_id, card in cards.items():
        cards[card_id]['uploaded_img_url'] = False
    with open(db_file, 'w') as db:
        yaml.dump(cards, db)
        
def set_schedule():
    '''Set daily and weekly schedules.'''
    if test:
        chara_card_num = 6      # sometimes become 6
        for t in range(chara_card_num):
            now = datetime.now()
            sched.add_date_job(run, now + timedelta(seconds=t*5+10), args=['daily'])
    if quick:
        for t in range(12):
            now = datetime.now()
            sched.add_date_job(run, now + timedelta(seconds=t*10+10), args=['weekly'])
    if weekly:
        for t in range(11):
            now = datetime.now()
            # run('weekly') 12 times every 5 minutes
            sched.add_date_job(run, now + timedelta(minutes=t*5, seconds=10), args=['weekly']) 
    sched.print_jobs()
    signal.pause()  # not to let program exit

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
        title = re.search(r'(.+) : ', title).group(1)
    return title
    
def check_update():
    '''check DCD news and tweet the information'''
    url_base = 'http://precure-live.com'
    r = requests.get('http://precure-live.com/allstars/')
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text)
    # extract only new news items
    news = soup(id='precure-news')[0].span.findParent().findNextSiblings()
    new_news = ''
    for i in news:
        if i.has_attr('class'):
            break
        new_news += str(i)
    news = BeautifulSoup(''.join(new_news))
    news = news('a', class_=re.compile(r'^news.*'))
    with open(last_news_file) as f:
        last_news = f.read().split('\n')
    new = False
    for i in news:
        if not str(i) in last_news:
            new = True
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
            print('プリキュアDCDの「{category}」のページが更新されましたわ！ | {title} - {url}'.format(category=category, title=title, url=url))
            tweet('プリキュアDCDの「{category}」のページが更新されましたわ！ | {title} - {url}'.format(category=category, title=title, url=url))

    if new: # write new last news list
        with open(last_news_file, 'w') as f:
            for i in news:
                f.write(str(i) + '\n')

if __name__ == '__main__':
    
    docs = '''\
Usage:
  {0} [test] [quick] <command> <arguments>
command:
  run                     Run que tweet.
  set_schedule            Run scheduler.
  clear		          Crear all the uploaded_img_url from database.
  make_que [weekly]       Make ques.yaml for daily[weekly] tweets.
  tweet <args>            Tweet <args> text.
  timeline <args>         Show home timeline.
  img <img> <args>        Tweet <args> text with <img> image file.
  check_update            Check website update.'''.format(basename(sys.argv[0]))
    
    test = False
    quick = False
    weekly = False
    args = sys.argv[1:]
    if len(args) < 1:
        print(docs)
        exit()
    elif args[0] == 'test':
        test = True
        cred_file = '.credentials_for_test'
        args.pop(0)
    elif args[0] == 'quick':
        quick = True
        args.pop(0)
    elif args[0] == 'weekly':
        weekly = True
        args.pop(0)

    if len(args) < 1:
        print(docs)
    elif args[0] == 'tweet':
        tweet(status=args[1:])
        if args[1] == 'img':
            tweet(status=args[2:],img_path=args[1])
    elif args[0] == 'timeline':
        get_timeline()
    elif args[0] == 'clear':
        clear_uploaded_img_url()
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
    elif args[0] == 'set_schedule':
        set_schedule()
    elif args[0] == 'download':
        download()
    elif args[0] == 'check_update':
        check_update()
    elif args[0] == 'run':
        run()
