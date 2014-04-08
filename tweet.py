#!/usr/bin/env python3
from twython import Twython
from twitter import oauth_dance
import sys

def auth():
    '''
    authonticated the account and return twitter class
    '''
    # read app credentials
    app_creds = open('.app_credentials')
    app_key = app_creds.readline().rstrip()
    app_secret = app_creds.readline().rstrip()

    # read oauth credentials
    oauth_creds = open('.oauth_credentials')
    if not oauth_creds:
        oauth_dance("precure-today-cards", app_key, app_secret,
                    '.oauth_credentials')
    oauth_token = oauth_creds.readline().rstrip()
    oauth_secret = oauth_creds.readline().rstrip()
    return Twython(app_key, app_secret, oauth_token, oauth_secret)

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
        print('''Usage:
    {0} <command> <arguments>
Example:
    {0} tweet <args> -> tweet <args> text.
    {0} img <arg1> <args> -> tweet <args> text with <arg1> image file.
        '''.format(sys.argv[0]))
    
    elif args[0] == 'tweet':
        tweet(status=args[1:])
    elif args[0] == 'img':
        tweet(status=args[2:],img_path=args[1])
