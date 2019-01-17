# pics
In one tab, start redis-server<br>

In another tab, start celery worker:<br>
	cd ~/dev/pics/mysite<br>
	celery -A pics worker --loglevel=info<br>

In a third tab, start django:<br>
	cd ~/dev/pics/mysite<br>
	python manage.py runserver localhost:8000<br>

<p>
Functions:
<ul>
<li>	Update Picture Database: builds the pictures database with information about all public photos
<li>
	Download Pictures: downloads pictures from the pictures database meeting certain criteria (currently > 100 views or tagged as "wallpaper"
<li>
	Process Slides: Adds title and date text to the downloaded pictures
<li>
	Individual pictures can be updated from the admin UI (for example, after editing the title or date taken on flickr)
</ul>
