from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Sum
from .models import Photo, NoWallpaper
from .flickr_utils import (flickr_keys, flickr_connect, get_flickr_photo,
                           get_flickr_small)
import flickrapi
import flickrapi.shorturl
import flickrapi.exceptions
import requests
import json
import os
import time
from .tasks import update_pics_db, rebuild_pics_db, download_pics_task, process_slides_task
from .forms import SearchPicturesForm
from pics.settings import DOWNLOAD_PATH

def index(request):
    total_views = Photo.total_views()
    public_pictures = Photo.objects.count()
    eligible = Photo.slideshow_count()
    actual = len([name for name in os.listdir(DOWNLOAD_PATH) if os.path.isfile(os.path.join(DOWNLOAD_PATH, name))])
    context = {'total_views': total_views, 
               'public_pictures': public_pictures, 
               'eligible': eligible,
               'actual': actual}
    return render(request, 'pics/index.html', context=context)

def update_db(request):
    result = update_pics_db.delay()
    return render(request, 'pics/update_db.html', context={'task_id': result.task_id})

def rebuild_db(request):
    result = rebuild_pics_db.delay()
    return render(request, 'pics/rebuild_db.html', context={'task_id': result.task_id})

def download_pics(request):
    result = download_pics_task.delay()
    return render(request, 'pics/download_pics.html', context={'task_id': result.task_id})

def process_slides(request):
    result = process_slides_task.delay()
    return render(request, 'pics/process_slides.html', context={'task_id': result.task_id})

def search_pictures(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = SearchPicturesForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            picture_list = Photo.objects.all().order_by('date_taken')
            search_string = form.cleaned_data['search_text']
            if search_string and search_string != '':
                picture_list = picture_list.filter(title__icontains=search_string)
            start_date = form.cleaned_data['start_date']
            if start_date:
                picture_list = picture_list.filter(date_taken__gte=start_date)
            end_date = form.cleaned_data['end_date']
            if end_date:
                picture_list = picture_list.filter(date_taken__lte=end_date)
            
            return render(request, 'pics/picture_list.html', {'picture_list': picture_list})

    # if a GET (or any other method) we'll create a blank form
    else:
        form = SearchPicturesForm()

    return render(request, 'pics/search_pictures.html', {'form': form, 'picture_list': []})

def picture_info(request, pic_id):
    context = {}
    photo = Photo.objects.get(pic_id=pic_id)
        
    flickr = flickr_connect()
    info_dict = get_flickr_photo(flickr, photo.pic_id)
    if os.path.isfile(photo.image_path()):
        context['local'] = True
    else:
        context['local'] = False
    context['tags'] = []
    for entry in info_dict['photo']['tags']['tag']:
        context['tags'].append(entry['raw'])
    context['desc'] = info_dict['photo']['description']['_content']
    if context['desc'] is None or context['desc'] == '':
        context['desc'] = 'None'
    context['title'] = info_dict['photo']['title']['_content']
    context['date_taken'] = photo.display_date()
    context['url'] = get_flickr_small(flickr, photo.pic_id)
    context['view_count'] = photo.view_count
    if NoWallpaper.objects.filter(pic_id=pic_id).count() != 0:
        context['excluded'] = True
        context['included'] = False
    else:
        context['excluded'] = False
        if photo.wallpaper is True:
            context['included'] = True
        else:
            context['included'] = False
    return render(request, 'pics/picture_info.html', context=context)