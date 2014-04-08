#!/usr/bin/env python3
import pickle
import sys
import signal
import pandas as pd
from datetime import datetime, timedelta
from os.path import basename
from apscheduler.scheduler import Scheduler
from tweet import tweet
from img_downloader import download_cards
import generator

db_file = 'cards.csv'
que_file = 'ques.p'

sched = Scheduler()
sched.start()

def tweet(mode='daily'):
    '''Read ques, tweet a tweet, and write ques'''
    with open(que_file, 'rb') as f:
        ques = pickle.load(f)
    if len(ques) == 1:
        generator.make_que(mode)
    que = ques.popleft()

    status = generator.tweet_generator(*que)
    if sys.argv[1] == 'test':
        print('status:', status)
    else:
        res = tweet(**status)
        # update db
        uploaded_img_url = res['entities']['media'][0]['url']
        cards = pd.read_csv(db_file)
        filename = basename(img_path)
        cards.loc[cards['filename'] == filename, 'uploaded_img_url'] = uploaded_img_url
        cards.to_csv(db_file, index=False)
    
    with open(que_file, 'wb') as f:
        pickle.dump(ques, f)
    sched.print_jobs()

def download():
    '''Try download cards until updated and set weekly tweet'''
    res = download_cards()
    res = 0
    while(res): # when the page is not updated
        time.sleep(60)
        res = download_cards()
    
def main():
    '''Set daily and weekly schedules.'''
    # set daily tweet schedule
    sched.add_cron_job(tweet, hour='9,21', args=['daily'])

    # set download schedule
    sched.add_cron_job(download, day_of_week='thu')
    download()
    
    # set weekly tweet schedule
    generator.make_que('weekly')
    now = datetime.now()
    for t in range(0, 60, 5):
        if sys.argv[1] == 'test':
            sched.add_date_job(tweet, now + timedelta(seconds=t+1), args=['weekly'])
        else:
            sched.add_date_job(tweet, now + timedelta(minutes=t, seconds=10), args=['weekly'])
    sched.print_jobs()

    signal.pause()      # not to let program exit
        
if __name__ == '__main__':
    main()
