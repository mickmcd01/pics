# pics
In one tab, start redis-server<br>

In another tab, start celery worker:<br>
	cd ~/dev/pics/mysite<br>
	celery -A pics worker --loglevel=info<br>

In a third tab, start django:<br>
	cd ~/dev/pics/mysite<br>
	python manage.py runserver localhost:8000<br>
