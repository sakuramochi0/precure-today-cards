#!/usr/bin/env python3
import os
from os import path
import re
import yaml
import requests
from bs4 import BeautifulSoup

save_dir = 'img/'

# construct filename dictionary
filename_file = 'filename.yaml'
if path.exists(filename_file):
    with open(filename_file) as f:
        filename = yaml.load(f)
else:
    page_num = 1
    filename = dict()
    while True:
        url = 'http://ux.getuploader.com/curecode/thumbnail/{}/date/desc'.format(page_num)
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
        urls = [a['href'] for a in soup(id='thumbnail')[0]('a')]
        if not urls:
            print('get all page')
            break
        for url in urls:
            num, name = re.search('/(\d+)/(.+\.(png|jpg))$', url).groups()[:2]
            filename[num] = name
            print('filename[{}] = {}'.format(num, name))
        page_num += 1
    with open(filename_file, 'w') as f:
        yaml.dump(filename, f)
        
# download
for i in range(1, 739):
    if str(i) not in filename:
        continue
    if not path.exists(save_dir):
        os.mkdir(save_dir)
    filepath = 'uploader/' + filename[str(i)]
    if not path.exists(filepath):
        for server in ['dl6', 'dl1', 'download1', 'download2', 'download4', 'download5']:
            r = requests.get('http://{}.getuploader.com/g/curecode/{}/download'.format(server, i))
            if len(r.content):
                break

        with open(filepath, 'wb') as f:
            if not len(r.content):
                print('Not found file. Check server name http://ux.getuploader.com/curecode/download/' + str(i))
            f.write(r.content)
            print('save', filename[str(i)])
