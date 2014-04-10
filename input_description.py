#!/usr/bin/env python3
# input_description.py - help to input insufficient infomation in the card db
from PIL import Image
import yaml
import easygui as eg

img_dir = 'img/'
db_file = 'cards.yaml'

with open(db_file) as db:
    cards = yaml.load(db)
for card in cards:
    if str(card['chara_name']) == '': # if comment is empty
        filename = card['filename']
        img = Image.open(img_dir + filename)
        img.show()
        msg = 'カードのデータを入力してね♪'
        title = 'カードデータの入力'
        field_names = ['キャラクター', 'カード名', 'キャラクター', 'コメント']
        field_values = []
        field_values = eg.multenterbox(msg, title, field_names)
        chara_name, card_name, comment_name, comment = field_values[:]
        if not chara_name:
            chara_name = 'リボン'
        cards['chara_name'] = chara_name
        cards['card_name'] = card_name
        cards['comment_name'] = comment_name
        cards['filename'] = filename
        with open(db_file) as db:
            yaml.dump(cards, db)
