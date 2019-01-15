import flickrapi
import flickrapi.shorturl
import flickrapi.exceptions
import requests
import json
import os
import time
from celery import shared_task
from pics.models import Photo
from pics.settings import (VIEW_THRESHOLD, DOWNLOAD_PATH, FONT_PATH,
                           TEST_LIMIT)
from pics.flickr_utils import connect, disconnect, flickr_keys
from celery import Celery
from celery_progress.backend import ProgressRecorder
from PIL import Image, ImageFont, ImageDraw, ExifTags, ImageFile

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

@shared_task(bind=True)
def update_pics_db(self):
    """Load the database with information on all of the pictures
    in flickr.
    """
    keys = flickr_keys()
    flickr = flickrapi.FlickrAPI(keys['api_key'], keys['api_secret'])

    progress_recorder = ProgressRecorder(self)
    total = Photo.objects.count()
    progress = 0

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
        progress_recorder.set_progress(progress, total)
        if progress < total:
            progress += 1
        if TEST_LIMIT > 0 and progress > TEST_LIMIT:
            break
    progress_recorder.set_progress(total, total)
    return True

@shared_task(bind=True)
def download_pics_task(self):
    """Download pictures from flickr that have greater than
    100 views or are marked as wallpaper
    """
    progress_recorder = ProgressRecorder(self)
    total = 0
    progress = 0

    photos = Photo.objects.all()
    for photo in photos:
        if photo.view_count > VIEW_THRESHOLD or photo.wallpaper is True:
            total += 1

    for photo in photos:
        if photo.view_count > VIEW_THRESHOLD or photo.wallpaper is True:
            _, tail = os.path.split(photo.source_url)
            dest_file = os.path.join(DOWNLOAD_PATH, tail)
            if not os.path.isfile(dest_file):
                r = requests.get(photo.source_url)
                with open(dest_file, "wb") as pic_file:
                    pic_file.write(r.content)
            progress += 1
            progress_recorder.set_progress(progress, total)
    progress_recorder.set_progress(total, total)

@shared_task(bind=True)
def process_slides_task(self):
    """Process the files in the slideshow directory: add the title
    text and rotate if necessary.
    """
    progress_recorder = ProgressRecorder(self)
    total = 0
    progress = 0

    photo_info = {}
    # create a dictionary for each of the pictures
    photos = Photo.objects.all()
    for photo in photos:
        _, tail = os.path.split(photo.source_url)
        photo_info[tail] = (photo.title, photo.date_taken.strftime('%B %d, %Y'))

    filelist = os.listdir(DOWNLOAD_PATH)
    total = len(filelist)
    img_fraction = 0.02

    for filename in os.listdir(DOWNLOAD_PATH):
        img_path = os.path.join(DOWNLOAD_PATH, filename)
        img = Image.open(img_path)

        # rotate the picture if needed
        for orientation in ExifTags.TAGS.keys(): 
            if ExifTags.TAGS[orientation]=='Orientation':
                break 

        e = img._getexif()
        if e:
            exif = dict(e.items())
            if exif:
                try:
                    orient = exif[orientation]
                    if orient == 3:  
                        img = img.transpose(Image.ROTATE_180)
                    elif orient == 6: 
                        img = img.transpose(Image.ROTATE_270)
                    elif orient == 8: 
                        img = img.transpose(Image.ROTATE_90)
                except:
                    pass

        # add the title and the date and save. put it in a try/except
        # deal with "image truncated" errors from PIL
        try:
            draw = ImageDraw.Draw(img)
            font_size = 32
            font = ImageFont.truetype(FONT_PATH, font_size)

            title = photo_info[filename][0]
            date = photo_info[filename][1]

            while font.getsize(title)[1] < img_fraction * img.size[1]:
                font_size += 2
                font = ImageFont.truetype(FONT_PATH, font_size)

            margin = font.getsize(title)[1]
            line_2 = (margin * 1.5) + font.getsize(title)[1]

            # border
            draw.text((margin-2, margin-2), title, font=font, fill='black')
            draw.text((margin+2, margin-2), title, font=font, fill='black')
            draw.text((margin-2, margin+2), title, font=font, fill='black')
            draw.text((margin+2, margin+2), title, font=font, fill='black')

            draw.text((margin-2, line_2-2), date, font=font, fill='black')
            draw.text((margin+2, line_2-2), date, font=font, fill='black')
            draw.text((margin-2, line_2+2), date, font=font, fill='black')
            draw.text((margin+2, line_2+2), date, font=font, fill='black')

            # fill
            draw.text((margin, margin), title, font=font, fill='white')
            draw.text((margin, line_2), date, font=font, fill='white')

            # save
            img.save(img_path, quality=95)
        except:
            pass

        progress += 1
        progress_recorder.set_progress(progress, total)

    progress_recorder.set_progress(total, total)