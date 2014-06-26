#!/usr/bin/env python3
# input_description.py - help to input insufficient infomation in the card db
from PIL import Image
import yaml
import easygui as eg

img_dir = 'img/'
db_file = 'cards.yml'

with open(db_file) as db:
    cards = yaml.load(db)
cs = cards # avoid from RuntimeError: dictionary changed size during iteration
for id, card in cs.items():
    if not (('chara_name' in card.keys()) and ('card_name' in card.keys()) \
            and ('comment_name' in card.keys()) and ('comment' in card.keys())):
        filename = card['filename']
        img = Image.open(img_dir + filename)
        img.show()
        msg = 'カードのデータを入力してね♪'
        title = 'カードデータの入力'
        field_names = ['キャラクター', 'なまえ', 'カード名', 'コメント']
        field_values = []
        field_values = eg.multenterbox(msg, title, field_names)
        chara_name, comment_name, card_name, comment = field_values[:]
        if not chara_name:
            chara_name = 'リボン'
        cards[id]['chara_name'] = chara_name
        cards[id]['card_name'] = card_name
        cards[id]['comment_name'] = comment_name
        cards[id]['comment'] = comment
        print('write: {}'.format(field_values[:]))
        with open(db_file, 'w') as db:
            yaml.dump(cards, db, allow_unicode=True)
