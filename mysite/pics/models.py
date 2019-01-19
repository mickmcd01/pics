import flickrapi
import flickrapi.shorturl
import flickrapi.exceptions
import time
import json
import os
import requests
import datetime
from django.db import models
from django.db.models import Sum
from pics.settings import DOWNLOAD_PATH, VIEW_THRESHOLD

class Statistics(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    public_pics = models.IntegerField('public_pics')
    view_count = models.IntegerField('view_count')
    edits = models.IntegerField('edits')

    class Meta:
        verbose_name_plural = 'Statistics'

    @staticmethod
    def create(edits):
        stats = Statistics()
        stats.public_pics = Photo.objects.count()
        stats.view_count = Photo.total_views()
        stats.edits = edits
        stats.save()

class Photo(models.Model):
    pic_id = models.CharField(max_length=50, primary_key=True)
    date_posted = models.DateTimeField('date posted')
    date_taken = models.DateTimeField('date taken')
    date_updated = models.DateTimeField('date updated')
    view_count = models.IntegerField('views')
    source_url = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    wallpaper = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def download_from_flickr(self):
        _, tail = os.path.split(self.source_url)
        dest_file = os.path.join(DOWNLOAD_PATH, tail)
        r = requests.get(self.source_url)
        with open(dest_file, "wb") as pic_file:
            pic_file.write(r.content)

    def image_path(self):
        _, tail = os.path.split(self.source_url)
        path = os.path.join(DOWNLOAD_PATH, tail)
        return path

    def display_date(self):
        return self.date_taken.strftime('%B %d, %Y')

    @staticmethod
    def total_views():
        total_views = Photo.objects.aggregate(Sum('view_count'))
        return total_views['view_count__sum']

    @staticmethod
    def create_or_update(photo_id, flickr_info):
        photo = None
        return_value = ''
        views_changed = False
        try:
            photo = Photo.objects.get(pic_id=photo_id)
            if photo.view_count != int(flickr_info['views']):
                photo.view_count = int(flickr_info['views'])
                views_changed = True
            title = flickr_info['title']
            # quotes in the title confuse things
            title = title.replace("'", '')
            title = title.replace('"', '')
            if title != photo.title:
                photo.title = title
                return_value = 'edit'
            old_date = photo.date_taken.strftime('%Y-%m-%d %H:%M:%S')
            if old_date != flickr_info['datetaken']:
                photo.date_taken = '%s+00' % flickr_info['datetaken']
                return_value = 'edit'
            if photo.wallpaper is False:
                tags = flickr_info['tags'].split()
                for tag in tags:
                    if tag == 'wallpaper':
                        photo.wallpaper = True
                        return_value = 'edit'
                        break
            if views_changed or return_value == 'edit':
                photo.save()
        except Photo.DoesNotExist:
            return_value = 'create'
            photo = Photo()
            photo.pic_id = photo_id
            title = flickr_info['title']
            # quotes in the title confuse things
            title = title.replace("'", '')
            title = title.replace('"', '')
            photo.title = flickr_info['title']
            photo.date_taken = '%s+00' % flickr_info['datetaken']
            photo.date_posted = time.strftime('%Y-%m-%d %H:%M:%S+00', time.localtime(
                                    int(flickr_info['dateupload'])))
            photo.date_updated = time.strftime('%Y-%m-%d %H:%M:%S+00', time.localtime(
                                    int(flickr_info['lastupdate'])))
            photo.view_count = int(flickr_info['views'])
            tags = flickr_info['tags'].split()
            for tag in tags:
                if tag == 'wallpaper':
                    photo.wallpaper = True
                    break
            photo.source_url = flickr_info['url_o']
            photo.save()
        return return_value

    def in_slideshow(self):
        if self.view_count >= VIEW_THRESHOLD or self.wallpaper:
            return True
        else:
            return False
    
    @staticmethod
    def slideshow_count():
        count = 0
        photos = Photo.objects.all()
        for photo in photos:
            if photo.in_slideshow() is True:
                count += 1
        return count
