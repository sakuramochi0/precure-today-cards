#!/usr/bin/env python3
# generate_html.py - generate a html which presents a list of all the images in the img dir.
import re
import glob
from os import path
import yaml
from bs4 import BeautifulSoup

with open('cards.yml') as f:
    cards = yaml.load(f)
with open('filename.yml') as f:
    filenames = yaml.load(f)
with open('template.html') as f:
    template = f.read()

def sort_name(items):
    filename = items[1]
    if not re.search('^\d', filename):
        match = re.search('(img_card_hapiness)(\d+)-(\d+)', filename)
        filename = match.group(1) + match.group(2) + '{:03d}'.format(int(match.group(3)))
    return filename

thumbs = []
#for num, filename in reversed(sorted(filenames.items(), key=sort_name)):
soup = BeautifulSoup()
thumbs = soup.new_tag('div')
for filename in reversed(sorted(glob.glob('img/jpg/*'))):
    card = [card for _, card in cards.items() if path.basename(card['filename'][:-3]) == path.basename(filename[:-3])]
    if card:
        card = card[0]
    outer_box = soup.new_tag('div')
    outer_box['class'] = 'outer-box'
    box = soup.new_tag('div')
    box['class'] = 'box'
    a = soup.new_tag('a')
    a['href'] = filename
    a['rel'] = 'imgs'
    img = soup.new_tag('img')
    img['src'] = '/img/1x1.png'
    img['data-original'] = filename
    img['class'] = 'lazy'
    a.append(img)
    box.append(a)
    outer_box.append(box)
    if card and 'comment' in card and card['comment']: # if there is data, comment must be input     
        outer_box.append('{} / {}'.format(card['chara_name'], card['card_name']))
        outer_box.append(soup.new_tag('br'))
        outer_box.append('{}「{}」'.format(card['comment_name'], card['comment']))
    thumbs.append(outer_box)

html = template.format(thumbs=thumbs.prettify())
#print(html)
    
with open('html/index.html', 'w') as f:
    f.write(html)

