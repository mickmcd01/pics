from django.http import HttpResponse
from django.shortcuts import render
from .models import Photo
from .flickr_utils import connect, disconnect, flickr_keys
import flickrapi
import flickrapi.shorturl
import flickrapi.exceptions
import requests
import json
import os
import time
from .tasks import update_pics_db, download_pics_task, process_slides_task

def index(request):
    return render(request, 'pics/index.html')

def update_db(request):
    result = update_pics_db.delay()
    return render(request, 'pics/update_db.html', context={'task_id': result.task_id})

def download_pics(request):
    result = download_pics_task.delay()
    return render(request, 'pics/download_pics.html', context={'task_id': result.task_id})

def process_slides(request):
    result = process_slides_task.delay()
    return render(request, 'pics/process_slides.html', context={'task_id': result.task_id})
