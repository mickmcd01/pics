import flickrapi
import flickrapi.shorturl
import flickrapi.exceptions
import requests
import json
import os
import time
from celery import shared_task
from pics.models import Photo, Statistics
from pics.settings import (VIEW_THRESHOLD, DOWNLOAD_PATH, FONT_PATH,
                           TEST_LIMIT, FLICKR_USER_ID)
from pics.flickr_utils import (flickr_connect, get_flickr_photo, 
                               get_public_count)
from celery import Celery
from celery_progress.backend import ProgressRecorder
from PIL import Image, ImageFont, ImageDraw, ExifTags, ImageFile

app = Celery('tasks', broker='redis://localhost')
app.conf.broker_url = 'redis://localhost:6379/0'

def final_processing(img_path, title, date):
    """Add title and date to a photo. If necessary,
    rotate the photo as well.
    """
    img_fraction = 0.02
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
        return True
    except:
        return False

def update_one_record(photo):
    flickr = flickr_connect()
    info_dict = get_flickr_photo(flickr, photo.pic_id)

    title = info_dict['photo']['title']['_content']
    # quotes in the title confuse things
    title = title.replace("'", '')
    title = title.replace('"', '')
    photo.title = title

    photo.date_taken = '%s+00' % info_dict['photo']['dates']['taken']
    photo.view_count = int(info_dict['photo']['views'])

    photo.save()

def update_db_from_flickr(self, rebuild):
    """Load the database with information on all of the pictures
    in flickr.
    """
    flickr = flickr_connect()

    progress_recorder = ProgressRecorder(self)

    if TEST_LIMIT > 0:
        total = TEST_LIMIT
    else:
        total = get_public_count(flickr)
    progress = 0

    # on a rebuild, delete the info currently in the table
    if rebuild is True:
        Photo.objects.all().delete()

    edit_count = 0

    for photo in flickr.walk(user_id=FLICKR_USER_ID):
        photo_id = photo.get('id')
        retries = 5
        while retries > 0:
            try:
                info_dict = get_flickr_photo(flickr, photo_id)
                if info_dict['photo']['visibility']['ispublic'] == 1:
                    status = Photo.create_or_update(flickr, photo_id, info_dict)
                    if status == 'edit':
                        edit_count += 1
                retries = 0
            except flickrapi.exceptions.FlickrError:
                retries -= 1
                time.sleep(0.1)
        progress_recorder.set_progress(progress, total)
        if progress < total:
            progress += 1
        if TEST_LIMIT > 0 and progress >= TEST_LIMIT:
            break
    progress_recorder.set_progress(total, total)
    Statistics.create(edit_count)
    return

@shared_task(bind=True)
def update_pics_db(self):
    """Load the database with information on all of the pictures
    in flickr.
    """
    update_db_from_flickr(self, rebuild=False)
    return True


@shared_task(bind=True)
def rebuild_pics_db(self):
    """Load the database with information on all of the pictures
    in flickr.
    """
    update_db_from_flickr(self, rebuild=True)
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
            photo.download_from_flickr()
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
        photo_info[tail] = (photo.title, photo.display_date())

    filelist = os.listdir(DOWNLOAD_PATH)
    total = len(filelist)

    for filename in os.listdir(DOWNLOAD_PATH):
        img_path = os.path.join(DOWNLOAD_PATH, filename)
        final_processing(img_path, photo_info[filename][0], photo_info[filename][1])
        progress += 1
        progress_recorder.set_progress(progress, total)

    progress_recorder.set_progress(total, total)
