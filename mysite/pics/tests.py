import datetime
import pytz
from django.test import TestCase
from pics.models import Photo
from pics.settings import DOWNLOAD_PATH

class PhotoTestCase(TestCase):
    def setUp(self):
        Photo.objects.create(pic_id='0001', date_posted='2018-12-01 00:00:00+00',
            date_taken='2018-12-01 00:00:00+00', date_updated='2018-12-01 00:00:00+00',
            view_count=100, source_url='https://www.flickr.com/test_photo_1_o.jpg',
            title='Test Photo 1', wallpaper=False)

    def test_image_path(self):
        photo = Photo.objects.get(pic_id='0001')
        path = photo.image_path()
        self.assertEqual(path, '%s/%s' % (DOWNLOAD_PATH, 'test_photo_1_o.jpg'))

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
