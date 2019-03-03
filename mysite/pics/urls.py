from django.urls import path, include
from django.contrib import admin
from pics import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pics/rebuild_db', views.rebuild_db, name='rebuild_db'),
    path('pics/update_db', views.update_db, name='update_db'),
    path('pics/preview_missing', views.preview_missing, name='preview_missing'),
    path('pics/download_and_process', views.download_and_process, name='download_and_process'),
    path('pics/download_pics', views.download_pics, name='download_pics'),
    path('pics/process_slides', views.process_slides, name='process_slides'),
    path('pics/search_pictures', views.search_pictures, name='search_pictures'),
    path('pics/picture_info/<int:pic_id>', views.picture_info, name='picture_info'),
    path('pics/', views.index, name='index'),
    path('celery-progress/', include('celery_progress.urls')),
]