import flickrapi
import flickrapi.shorturl
import flickrapi.exceptions
import requests
import json
import os
import time
from celery.decorators import task
from pics.models import Photo
from pics.flickr_utils import connect, disconnect, flickr_keys
from celery import Celery

app = Celery('tasks', broker='redis://localhost')
app.conf.broker_url = 'redis://localhost:6379/0'

def process_one_photo(flickr, photo_id, info_dict):
    """Process one photo: using the metadata for the photo,
    put the relevant information into the database.
    """
    photo = Photo()
    photo.pic_id = photo_id
    title = info_dict['photo']['title']['_content']
    # quotes in the title confuse things
    title = title.replace("'", '')
    title = title.replace('"', '')
    photo.title = title
    photo.date_taken = '%s+00' % info_dict['photo']['dates']['taken']
    photo.date_posted = time.strftime('%Y-%m-%d %H:%M:%S+00', time.localtime(
                            int(info_dict['photo']['dates']['posted'])))
    photo.date_updated = time.strftime('%Y-%m-%d %H:%M:%S+00', time.localtime(
                             int(info_dict['photo']['dates']['lastupdate'])))
    photo.view_count = int(info_dict['photo']['views'])
    tags = info_dict['photo']['tags']
    for tag in tags['tag']:
        if tag['raw'] == 'wallpaper':
            photo.wallpaper = True
            break

    retries = 5
    photo.source_url = None
    while retries > 0:
        try:
            sizes = flickr.photos.getSizes(photo_id=photo_id,
                                           format='json')
            retries = 0
            sizes_dict = json.loads(sizes.decode("utf-8"))
            source = None
            for entry in sizes_dict['sizes']['size']:
                if entry['label'] == 'Original':
                    photo.source_url = entry['source']
                    break
        except flickrapi.exceptions.FlickrError:
            retries -= 1
            time.sleep(0.1)
    
    if photo.source_url:
        photo.save()

@app.task(name="update_pics_db")
def update_pics_db(request):
    """Load the database with information on all of the pictures
    in flickr.
    """
    keys = flickr_keys()
    flickr = flickrapi.FlickrAPI(keys['api_key'], keys['api_secret'])

    # delete the info currently in the table
    Photo.objects.all().delete()

    for photo in flickr.walk(user_id='mickmcd'):
        photo_id = photo.get('id')
        retries = 5
        while retries > 0:
            try:
                info = flickr.photos.getInfo(photo_id=photo_id, format='json')
                info_dict = json.loads(info.decode("utf-8"))
                if info_dict['photo']['visibility']['ispublic'] == 1:
                    process_one_photo(flickr, photo_id, info_dict)
                retries = 0
            except flickrapi.exceptions.FlickrError:
                retries -= 1
                time.sleep(0.1)
    return True