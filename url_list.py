#!/usr/bin/env python3
import yaml

with open('cards.yaml') as f:
    cards = yaml.load(f)
urls = []
for id, card in cards.items():
    urls.append(card['img_url'])
urls.sort()
with open('url-list.txt', 'w') as f:
    f.write('\n'.join(urls))
