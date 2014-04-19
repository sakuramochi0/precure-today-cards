#!/usr/bin/env python3
import sys
import signal
import yaml
from os.path import basename
from datetime import datetime, timedelta
from apscheduler.scheduler import Scheduler
from img_downloader import download_cards
import generator
from twython import Twython

db_file = 'cards.yaml'
que_file = 'ques.yaml'
cred_file = '.credentials'

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
    print('from ques:', ques)
    print('pop:', que)
    with open(que_file, 'w') as q:
        yaml.dump(ques, q)

def download():
    '''Try download cards until updated and set weekly tweet'''
    get_new_card = download_cards()
    if get_new_card:
        tweet('今日のカードが更新されましたわ！')
        generator.make_que('weekly')  # set weekly tweet schedule
        now = datetime.now()
        for t in range(0, 60, 5):
            # run('weekly') 12 times every 5 minutes
            sched.add_date_job(run, now + timedelta(minutes=t, seconds=10), args=['weekly']) 
        sched.print_jobs()
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
        for t in range(0, 6):
            now = datetime.now()
            sched.add_date_job(run, now + timedelta(seconds=t*5+10), args=['daily'])
    if quick:
        for t in range(12):
            now = datetime.now()
            sched.add_date_job(run, now + timedelta(seconds=t*10+10), args=['weekly'])
    sched.print_jobs()
    signal.pause()  # not to let program exit
        
if __name__ == '__main__':
    test = False
    quick = False
    args = sys.argv[1:]
    if len(args) < 1:
        print('''\
Usage:
  {0} <command> <arguments>
Example:
  {0} run                Run que tweet.
  {0} set_schedule       Run scheduler.
  {0} make_que [weekly]  Make ques.yaml for daily[weekly] tweets.
  {0} tweet <args>       Tweet <args> text.
  {0} timeline <args>    Show home timeline.
  {0} img <img> <args>   Tweet <args> text with <img> image file.'''.format(basename(sys.argv[0])))
    elif args[0] == 'test':
        test = True
        cred_file = '.credentials_for_test'
        args.pop(0)
    elif args[0] == 'quick':
        quick = True
        args.pop(0)
    if args[0] == 'tweet':
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
    elif args[0] == 'run':
        run()
