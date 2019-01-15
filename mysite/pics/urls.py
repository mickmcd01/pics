from django.urls import path, include
from django.contrib import admin
from pics import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pics/update_db', views.update_db, name='update_db'),
    path('pics/download_pics', views.download_pics, name='download_pics'),
    path('pics/process_slides', views.process_slides, name='process_slides'),
    path('pics/', views.index, name='index'),
    path('celery-progress/', include('celery_progress.urls')),
]