#!/usr/bin/env python3
import re
from os import path
import yaml

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
for num, filename in sorted(filenames.items(), key=sort_name):
    thumbs.append('<div class="box"><a href="jpg/{0}" rel="imgs"><img src="/img/1x1.png" data-original="jpg/{0}" class="lazy"></a></div>'.format(filename))

html = template.format(thumbs='\n\n'.join(thumbs))
    
with open(path.expanduser('~/www/precure/dcd-today-cards/index.html'), 'w') as f:
    f.write(html)
