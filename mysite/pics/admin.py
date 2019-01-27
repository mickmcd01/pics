import os
from subprocess import Popen
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from pics.models import Photo, Statistics
from pics.tasks import final_processing, update_one_record
from pics.flickr_utils import flickr_update_photo

class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'view_count', 'date_taken', 'wallpaper', 'show_photo_url')
    search_fields = ('title',)
    actions = ['update_photos', 'view_local_photo']
    readonly_fields = ['pic_id', 'date_posted', 'date_updated', 'view_count', 'source_url', 'wallpaper']

    def has_add_permission(self, request, obj=None):
        return False
        
    def save_model(self, request, obj, form, change):
        flickr_update_photo(obj)
        obj.download_from_flickr()
        path = obj.image_path()
        status = final_processing(path, obj.title, obj.display_date())
        if status is False:
            print('Failed!')
        super().save_model(request, obj, form, change)
    
    def update_photos(self, request, queryset):
        for obj in queryset:
            update_one_record(obj)
            obj.download_from_flickr()
            path = obj.image_path()
            status = final_processing(path, obj.title, obj.date_taken.split()[0])
            if status is False:
                print('Failed!')

    update_photos.short_description = "Update selected photos"

    def show_photo_url(self, obj):
        return format_html("<a href='{url}' target='_blank'>{url}</a>", url=obj.source_url)

    show_photo_url.short_description = "Photo on Flickr"

    def view_local_photo(self, request, queryset):
        for obj in queryset:
            if os.path.isfile(obj.image_path()): 
                Popen(['xviewer', obj.image_path()]) 

    view_local_photo.short_description = "View local photo"

admin.site.register(Photo, PhotoAdmin)

class StatisticsAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'public_pics', 'view_count', 'edits')

    def has_add_permission(self, request, obj=None):
        return False
        
admin.site.register(Statistics, StatisticsAdmin)    