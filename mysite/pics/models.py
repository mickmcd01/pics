import os
import requests
from django.db import models
from pics.settings import DOWNLOAD_PATH

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

