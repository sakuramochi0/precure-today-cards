#!/usr/bin/env python3
# img_downloader.py - get images, save them, and update database
import yaml
import requests
import re
import sys
import time
import datetime

img_dir = 'img/'
db_file = 'cards.yaml'

url_prefix = 'http://precure-live.com/allstars/'
page_url = url_prefix + 'precure-card/today-card.html'
headers = {'referer': url_prefix + 'index.html'}

def download_cards():
    '''download all card image of the week'''
    max_card_num = 12
    downloaded_list = []        # appended downloaded card_num
    retry = 0

    # read db
    with open(db_file) as db:
        cards = yaml.load(db)
    exist_filenames = []
    for card in cards.values():
        exist_filenames.append(card['filename'])
        
    # download all the card
    while len(downloaded_list) < max_card_num:
        retry += 1
        if retry > 100:
            print('- over 100 retry, exit')
            break
            
        # get html
        r = requests.get(page_url, headers=headers)

        # parse html & get img_url
        p = re.compile(r'image/precure-card/[^/]+/([^/]+)/([^"]+)')
        match = re.search(p, r.text)
        update_num = match.group(1)
        img_url = url_prefix + match.group()
        filename = match.group(2)

        # cf. filename: 'img_card_happiness01-68_e8d7824dxjm3.jpg'
        p = re.compile(r'img_card_(.+)(\d{2,})-(\d{2,})_(.+).jpg')
        match = re.search(p, filename)
        series = match.group(1)
        series_num = int(match.group(2))
        card_num = int(match.group(3))

        # prevent duplicated download
        if filename in exist_filenames:
            return False # not get new cards
        
        # check if the card is new or not
        if not card_num in downloaded_list:
            print('- get a new card #', len(downloaded_list) + 1)
            # get img
            r_img = requests.get(img_url, headers=headers)
            with open(img_dir + filename, 'wb') as f:
                f.write(r_img.content)
            print('- save image:', filename)
            
            downloaded_list.append(card_num)
            print('- add downloaded_list:', card_num)

            date = str(datetime.date.today())
            new_card = {'date': date,
                        'series': series,
                        'series_num': series_num,
                        'card_num': card_num,
                        'filename': filename,
                        'img_url': img_url,
                        'update_num': update_num}

            id = '{}-{}-{}'.format(series, series_num, card_num)
            cards[id] = new_card
            with open(db_file, 'w') as f:
                yaml.dump(cards, f)
            print('Append a record to the database:', card_num)
            print('-' * 8)
                            
        # safe access
        time.sleep(1)

    return True  # get new cards

def redownload():
    '''re-download all the images'''
    with open(db_file) as db:
        cards = yaml.load(db)
    for (id, card) in cards.items():
        img_url = card['img_url']
        filename = card['filename']
        r = requests.get(img_url, headers=headers)
        with open(img_dir + filename, 'wb') as f:
            f.write(r.content)
        print('Write image:', filename)
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == 'test':
            db_file = 'test.csv'
        elif sys.argv[1] == 'redownload':
            redownload()
    download_cards()
