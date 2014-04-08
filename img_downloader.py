#!/usr/bin/env python3
# img_downloader.py - get images, save them, and update database
import pandas as pd
import requests
import re
import sys
import io
import time
import datetime
from PIL import Image

img_dir = 'img/'
db_file = 'cards.csv'

def download_cards():
    '''download all card image of the week'''
    max_card_num = 12
    downloaded_list = []        # appended downloaded card_num
    retry = 0

    # read db
    cards = pd.read_csv(db_file)
    filenames = cards['filename'].tolist()
    
    # download all the card
    while len(downloaded_list) < max_card_num:
        retry += 1
        if retry > 100:
            print('- over 100 retry, exit')
            break
            
        print('fetching card #', len(downloaded_list) + 1)

        # get html
        url_prefix = 'http://precure-live.com/allstars/'
        page_url = url_prefix + 'precure-card/today-card.html'
        headers = {'referer': url_prefix + 'index.html'}
        r = requests.get(page_url, headers=headers)
        print('- fetch html')

        # parse html & get img_url
        p = re.compile(r'image/precure-card/[^/]+/[^/]+/([^"]+)')
        match = re.search(p, r.text)
        img_url = url_prefix + match.group()
        filename = match.group(1)
        print('- fetch image:\n    ', img_url)

        # cf. filename: 'img_card_happiness01-68_e8d7824dxjm3.jpg'
        p = re.compile(r'img_card_(.+)(\d{2,})-(\d{2,})_(.+).jpg')
        match = re.search(p, filename)
        series = match.group(1)
        series_num = int(match.group(2))
        card_num = int(match.group(3))

        # debug
        print('- parse filename:')
        print('    series:', series)
        print('    series_num:', series_num)
        print('    card_num:', card_num)

        # prevent duplicated download
        if filename in filenames:
            print('-' * 8)
            print('This weeks cards has already been downloaded.')
            print('-' * 8)
            return 1
        
        # check if the card is new or not
        if not card_num in downloaded_list:
            print('-' * 8)
            print('- get a new card')
            # get img
            r_img = requests.get(img_url, headers=headers)
            i = Image.open(io.BytesIO(r_img.content))
            i.save(img_dir + filename)
            print('- save image:', filename)
            
            downloaded_list.append(card_num)
            print('- add downloaded_list:', card_num)

            date = str(datetime.date.today())
            new_card = pd.DataFrame([[date,series,series_num,card_num,filename,img_url]],
                                    columns=['date','series','series_num','card_num','filename','img_url'])
            cards = cards.append([new_card])
            cards = cards.drop_duplicates()
            cards = cards.sort(['series', 'series_num', 'card_num'])
            cards = cards.fillna(0)
            cards.to_csv(db_file, index=False)
            print('Append a record to the database:', card_num)
                            
        # safe access
        print('-' * 8)
        time.sleep(3)

    return 0

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        db_file = 'test.csv'
    download_cards()
