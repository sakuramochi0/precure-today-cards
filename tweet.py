#!/usr/bin/env python3
from twython import Twython
import sys
from os.path import basename

cred_file = '.credentials'

def auth():
    '''
    authonticated the account and return twitter class
    '''
    # read app credentials
    with open(cred_file) as f:
        app_key, app_secret, oauth_token, oauth_secret = \
                            [x.strip() for x in f]
    t = Twython(app_key, app_secret, oauth_token, oauth_secret)
    return t

def get_timeline(user_id='precure_cards'):
    '''
    get twitter home timeline of the specific user
    '''
    t = auth()
    print('user_id: ', user_id)
    timeline = t.statuses.user_timeline(id=user_id)

    for line in timeline[:5]:
        print('{0[created_at]} {0[user][name]}({0[user][screen_name]}) {0[text]}'.format(line))

def tweet(status='', img_path=None):
    '''tweet a status text'''
    t = auth()
    if img_path:
        img = open(img_path, 'rb')
        res = t.update_status_with_media(status=status, media=img)
    else:
        res =t.update_status(status=status)
    return res

# for commandline
if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        print('''\
Usage:
  {0} <command> <arguments>
Example:
  {0} tweet <args>       tweet <args> text.
  {0} img <img> <args>  tweet <args> text with <img> image file.'''.format(basename(sys.argv[0])))
    elif sys.argv[1] == 'test':
        cred_file = '.credentials_for_test'
        sys.argv.pop(1)
    elif args[0] == 'tweet':
        tweet(status=args[1:])
    elif args[0] == 'img':
        tweet(status=args[2:],img_path=args[1])
