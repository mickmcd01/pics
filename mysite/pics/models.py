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
from pics.settings import DOWNLOAD_PATH

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
    def create_or_update(flickr, photo_id, info_dict):
        photo = None
        return_value = ''
        views_changed = False
        try:
            photo = Photo.objects.get(pic_id=photo_id)
            if photo.view_count != int(info_dict['photo']['views']):
                photo.view_count = int(info_dict['photo']['views'])
                views_changed = True
            title = info_dict['photo']['title']['_content']
            # quotes in the title confuse things
            title = title.replace("'", '')
            title = title.replace('"', '')
            if title != photo.title:
                photo.title = title
                return_value = 'edit'
                print('Titles: %s, %s' % (title, photo.title))
            old_date = time.strftime('%Y-%m-%d %H:%M:%S', photo.date_taken)
            if old_date != info_dict['photo']['dates']['taken']:
                print('Dates: %s, %s' % (old_date, info_dict['photo']['dates']['taken']))
                photo.date_taken = '%s+00' % info_dict['photo']['dates']['taken']
                return_value = 'edit'
            if photo.wallpaper is False:
                tags = info_dict['photo']['tags']
                for tag in tags['tag']:
                    if tag['raw'] == 'wallpaper':
                        photo.wallpaper = True
                        return_value = 'edit'
                        break
            if views_changed or return_value == 'edit':
                photo.save()
        except:
            return_value = 'create'
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
                    for entry in sizes_dict['sizes']['size']:
                        if entry['label'] == 'Original':
                            photo.source_url = entry['source']
                            break
                except flickrapi.exceptions.FlickrError:
                    retries -= 1
                    time.sleep(0.1)
            
            if photo.source_url:
                photo.save()
        return return_value    
