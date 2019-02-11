from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Sum
from .models import Photo
from .flickr_utils import flickr_keys
import flickrapi
import flickrapi.shorturl
import flickrapi.exceptions
import requests
import json
import os
import time
from .tasks import update_pics_db, rebuild_pics_db, download_pics_task, process_slides_task
from .forms import SearchPicturesForm

def index(request):
    total_views = Photo.total_views()
    public_pictures = Photo.objects.count()
    slideshow = Photo.slideshow_count()
    context = {'total_views': total_views, 'public_pictures': public_pictures, 'slideshow': slideshow}
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
            search_string = form.cleaned_data['search_text']
            picture_list = Photo.objects.filter(title__icontains=search_string).order_by('date_taken')
            return render(request, 'pics/picture_list.html', {'picture_list': picture_list})

    # if a GET (or any other method) we'll create a blank form
    else:
        form = SearchPicturesForm()

    return render(request, 'pics/search_pictures.html', {'form': form, 'picture_list': []})    