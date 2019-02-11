import os
from subprocess import Popen
from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from pics.models import Photo, Statistics, NoWallpaper
from pics.tasks import final_processing, update_one_record
from pics.flickr_utils import flickr_update_photo
from pics.settings import VIEW_THRESHOLD

class NoWallpaperAdmin(admin.ModelAdmin):
    list_display = ('pic_id', 'pic_info')
    actions = ['delete_nowallpaper']

    def delete_nowallpaper(self, request, queryset):
        attempted = len(queryset)
        successful = 0
        for obj in queryset:
            photo = Photo.objects.get(pic_id=obj.pic_id)
            if photo:
                if os.path.isfile(photo.image_path()): 
                    os.remove(photo.image_path())
                    successful += 1

        messages.info(request, 'Attempted to delete %d, actually deleted %d' % (attempted, successful)) 

    delete_nowallpaper.short_description = 'Delete "no wallpaper" photos'

    def pic_info(self, instance):
        photo = Photo.objects.get(pic_id=instance.pic_id)
        if photo:
            return '%s, %s' % (photo.title, photo.display_date())

    pic_info.short_description = 'Picture title and date taken'

admin.site.register(NoWallpaper, NoWallpaperAdmin)

class ViewCountListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = ('view count')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'view_count'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('less-than-threshold', ('less_than')),
            ('greater-than-threshold', ('greater_than')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'less-than-threshold':
            return queryset.filter(view_count__lt=VIEW_THRESHOLD)
        if self.value() == 'greater-than-threshold':
            return queryset.filter(view_count__gte=VIEW_THRESHOLD)

class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'view_count', 'date_taken', 'slideshow', 'show_flickr_page', 'show_photo_url')
    search_fields = ('title',)
    actions = ['update_photos', 'view_local_photo']
    readonly_fields = ['pic_id', 'date_posted', 'date_updated', 'view_count', 'source_url', 'wallpaper']
    ordering = ('-date_taken', )
    list_filter = (ViewCountListFilter,)

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

    def slideshow(self, obj):
        if NoWallpaper.objects.filter(pic_id=obj.pic_id).count() != 0:
            return 'Never'
        elif obj.wallpaper is True:
            return 'Always'
        else:
            return '-'

    slideshow.short_description = "Tagged"

    def show_photo_url(self, obj):
        return format_html("<a href='{url}' target='_blank'>Flickr Photo Only</a>", url=obj.source_url)

    show_photo_url.short_description = "Flickr Photo Only"

    def show_flickr_page(self, obj):
        return format_html("<a href='{url}' target='_blank'>Flickr Page</a>", url=obj.flickr_page())

    show_flickr_page.short_description = "Flickr Page"

    def view_local_photo(self, request, queryset):
        for obj in queryset:
            if os.path.isfile(obj.image_path()): 
                Popen(['xviewer', obj.image_path()])
            else:
                messages.error(request, 'There is no local file for %s' % obj.title) 

    view_local_photo.short_description = "View local photo"

admin.site.register(Photo, PhotoAdmin)

class StatisticsAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'public_pics', 'view_count', 'edits')
    readonly_fields = ['id', 'date', 'public_pics', 'view_count', 'edits']

    def has_add_permission(self, request, obj=None):
        return False
        
admin.site.register(Statistics, StatisticsAdmin)    