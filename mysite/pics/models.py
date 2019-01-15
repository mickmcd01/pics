from django.db import models

class Photo(models.Model):
    pic_id = models.CharField(max_length=50, primary_key=True)
    date_posted = models.DateTimeField('date posted')
    date_taken = models.DateTimeField('date taken')
    date_updated = models.DateTimeField('date updated')
    view_count = models.IntegerField('views')
    source_url = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    wallpaper = models.BooleanField(default=False)

