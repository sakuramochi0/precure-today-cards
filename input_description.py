#!/usr/bin/env python3
# input_description.py - help to input insufficient infomation in the card db
from PIL import Image
import pandas as pd
import easygui as eg

img_dir = 'img/'
db_file = 'cards.csv'

cards = pd.read_csv(db_file)
for card in cards.iterrows():
    c = card[1]
    if str(c['chara_name']) == 'nan': # if comment is empty
        filename = c['filename']
        img = Image.open(img_dir + filename)
        img.show()
        msg = 'カードのデータを入力してね'
        title = 'カードデータの入力'
        field_names = ['カードのキャラクター',
                       'カードの名前',
                       'コメントを言っているキャラクター',
                       'コメント']
        field_values = []
        field_values = eg.multenterbox(msg, title, field_names)
        chara_name, card_name, comment_name, comment = field_values[:]
        if not chara_name:
            chara_name = 'リボン'
            
        cards.loc[cards['filename'] == filename, 'chara_name'] = chara_name
        cards.loc[cards['filename'] == filename, 'card_name'] = card_name
        cards.loc[cards['filename'] == filename, 'comment_name'] = comment_name
        cards.loc[cards['filename'] == filename, 'comment'] = comment
        cards.to_csv(db_file, index=False)
