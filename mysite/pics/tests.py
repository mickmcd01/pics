import datetime
import pytz
from django.test import TestCase
from pics.models import Photo, Statistics
from pics.settings import DOWNLOAD_PATH

class PhotoTestCase(TestCase):
    def setUp(self):
        Photo.objects.create(pic_id='0001', date_posted='2018-12-01 00:00:00+00',
            date_taken='2016-07-11 00:00:00+00', date_updated='2018-12-01 00:00:00+00',
            view_count='100', source_url='https://www.flickr.com/test_photo_1_o.jpg',
            title='Test Photo 1', wallpaper=False)
        Photo.objects.create(pic_id='0003', date_posted='2018-12-01 00:00:00+00',
            date_taken='2018-12-01 00:00:00+00', date_updated='2018-12-01 00:00:00+00',
            view_count='1001', source_url='https://www.flickr.com/test_photo_3_o.jpg',
            title='Test Photo 3', wallpaper=False)

    def test_statistics(self):
        Statistics.create(5)
        stats = Statistics.objects.get(id=1)
        self.assertEqual(2, stats.public_pics)
        self.assertEqual(1101, stats.view_count)
        self.assertEqual(5, stats.edits)

    def test_image_path(self):
        photo = Photo.objects.get(pic_id='0001')
        path = photo.image_path()
        self.assertEqual(path, '%s/%s' % (DOWNLOAD_PATH, 'test_photo_1_o.jpg'))

    def test_total_views(self):
        self.assertEqual(1101, Photo.total_views())

    def test_display_date(self):
        photo = Photo.objects.get(pic_id='0001')
        self.assertEqual('July 11, 2016', photo.display_date())
        photo = Photo.objects.get(pic_id='0003')
        self.assertEqual('December 01, 2018', photo.display_date())

    def test_slideshow_count(self):
        Photo.objects.create(pic_id='0004', date_posted='2018-12-01 00:00:00+00',
            date_taken='2016-07-11 00:00:00+00', date_updated='2018-12-01 00:00:00+00',
            view_count='98', source_url='https://www.flickr.com/test_photo_1_o.jpg',
            title='Test Photo 4', wallpaper=False)
        Photo.objects.create(pic_id='0005', date_posted='2018-12-01 00:00:00+00',
            date_taken='2018-12-01 00:00:00+00', date_updated='2018-12-01 00:00:00+00',
            view_count='1001', source_url='https://www.flickr.com/test_photo_3_o.jpg',
            title='Test Photo 5', wallpaper=True)
        self.assertEqual(3, Photo.slideshow_count())

    def test_wallpaper_tag(self):
        Photo.objects.create(pic_id='0006', date_posted='2018-12-01 00:00:00+00',
            date_taken='2016-07-11 00:00:00+00', date_updated='2018-12-01 00:00:00+00',
            view_count='98', source_url='https://www.flickr.com/test_photo_1_o.jpg',
            title='Test Photo 6', wallpaper=False)
        photo = Photo.objects.get(pic_id='0006')
        self.assertEqual(False, photo.wallpaper)
        flickr_info = {'views':50, 'title':'Test Photo 6', 'datetaken':'2018-12-01 00:00:00',
                       'tags':'abc def wallxpaper', 'url_o': 'https://www.flickr.com/test_photo_2_o.jpg',
                       'dateupload':'1547931024', 'lastupdate':'1547931024'}
        photo.wallpaper_tag(flickr_info)
        self.assertEqual(False, photo.wallpaper)
        flickr_info = {'views':50, 'title':'Test Photo 6', 'datetaken':'2018-12-01 00:00:00',
                       'tags':'abc def wallpaper', 'url_o': 'https://www.flickr.com/test_photo_2_o.jpg',
                       'dateupload':'1547931024', 'lastupdate':'1547931024'}
        photo.wallpaper_tag(flickr_info)
        self.assertEqual(True, photo.wallpaper)

    def test_create_or_update(self):
        pic_id = '0002'
        flickr_info = {'views':50, 'title':'Test Photo 2', 'datetaken':'2018-12-01 00:00:00',
                       'tags':'abc def', 'url_o': 'https://www.flickr.com/test_photo_2_o.jpg',
                       'dateupload':'1547931024', 'lastupdate':'1547931024'}
        status = Photo.create_or_update(pic_id, flickr_info)
        self.assertEqual(status, 'create')
        flickr_info = {'views':55, 'title':'Test Photo 2', 'datetaken':'2018-12-01 00:00:00',
                       'tags':'abc def', 'url_o': 'https://www.flickr.com/test_photo_2_o.jpg',
                       'dateupload':'1547931024', 'lastupdate':'1547931024'}
        status = Photo.create_or_update(pic_id, flickr_info)
        self.assertEqual(status, '')
        flickr_info = {'views':55, 'title':'Modified Test Photo 2', 'datetaken':'2018-12-01 00:00:00',
                       'tags':'abc def', 'url_o': 'https://www.flickr.com/test_photo_2_o.jpg',
                       'dateupload':'1547931024', 'lastupdate':'1547931024'}
        status = Photo.create_or_update(pic_id, flickr_info)
        self.assertEqual(status, 'edit')
        flickr_info = {'views':55, 'title':'Modified Test Photo 2', 'datetaken':'2018-12-02 00:00:00',
                       'tags':'abc def', 'url_o': 'https://www.flickr.com/test_photo_2_o.jpg',
                       'dateupload':'1547931024', 'lastupdate':'1547931024'}
        status = Photo.create_or_update(pic_id, flickr_info)
        self.assertEqual(status, 'edit')
        photo = Photo.objects.get(pic_id=pic_id)
        self.assertEqual(photo.view_count, 55)
        self.assertEqual(photo.title, 'Modified Test Photo 2')
        self.assertEqual(photo.date_taken, datetime.datetime(2018, 12, 2, 0, 0, tzinfo=pytz.timezone("UTC")))
