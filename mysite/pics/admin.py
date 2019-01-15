from django.contrib import admin
from pics.models import Photo

class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'view_count', 'date_taken', 'wallpaper')

admin.site.register(Photo, PhotoAdmin)
