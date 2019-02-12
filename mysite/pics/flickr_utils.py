import os
import configparser
import json
import flickrapi
import time
from pics.settings import CONFIG_PATH, FLICKR_USER_NAME

def flickr_keys(filename=CONFIG_PATH):
    """Read the flickr key information."""
    # create a parser
    config = configparser.ConfigParser()
    # read config file
    config.read(filename)

    # get flickr api key and secret
    flickr_keys = {}
    if config.has_section('flickr'):
        params = config.items('flickr')
        for param in params:
            flickr_keys[param[0]] = param[1]
    else:
        raise Exception(
            'Section flickr not found in the {0} file'.format(filename))

    return flickr_keys


def flickr_connect():
    keys = flickr_keys()
    flickr = flickrapi.FlickrAPI(keys['api_key'], keys['api_secret'])
    return flickr


def get_flickr_photo(flickr, photo_id):
    info = flickr.photos.getInfo(photo_id=photo_id, format='json')
    info_dict = json.loads(info.decode("utf-8"))
    return info_dict

def get_flickr_small(flickr, photo_id):
    info = flickr.photos.getSizes(photo_id=photo_id, format='json')
    info_dict = json.loads(info.decode("utf-8"))
    for entry in info_dict['sizes']['size']:
        if entry['label'] == 'Small':
            return entry['source']
    return None

def get_public_count(flickr):
    info = flickr.people.findByUsername(username=FLICKR_USER_NAME, format='json')
    info = json.loads(info.decode('utf-8'))
    user_id = info['user']['nsid']
    info = flickr.people.getInfo(user_id=user_id, format='json')
    info = json.loads(info.decode('utf-8'))
    return info['person']['photos']['count']['_content']

def flickr_update_photo(obj):
    flickr = flickr_connect()
    flickr.authenticate_via_browser(perms='write')
    flickr.photos.setMeta(photo_id=obj.pic_id, title=obj.title)
    flickr.photos.setDates(photo_id=obj.pic_id, date_taken=obj.date_taken.strftime('%Y-%m-%d %H:%M:%S'))