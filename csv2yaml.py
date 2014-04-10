#!/usr/bin/env python3
import pandas as pd
import yaml
cs = pd.read_csv('cards.csv')
c = cs.to_dict()
n = {}
for i in range(len(c['filename'])):
    id = str(c['series'][i]) + '-' + str(c['series_num'][i]) + '-' + str(c['card_num'][i])
    n[id] = {}
    for key in c.keys():
        try:
            n[id][key] = int(c[key][i])
        except:
            n[id][key] = c[key][i]
        if n[id][key] == 0:
            n[id][key] = False
with open('cards.yaml', 'w') as f:
    yaml.dump(n, f)
