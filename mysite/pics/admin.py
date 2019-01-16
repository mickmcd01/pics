from django.contrib import admin
from django.utils.html import format_html
from pics.models import Photo

class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'view_count', 'date_taken', 'wallpaper', 'show_photo_url')
    search_fields = ('title',)
    
    def show_photo_url(self, obj):
        return format_html("<a href='{url}' target='_blank'>{url}</a>", url=obj.source_url)

    show_photo_url.short_description = "Photo on Flickr"

admin.site.register(Photo, PhotoAdmin)
