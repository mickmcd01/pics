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
<li>Update Picture Database: updates the pictures database, e.g. adds new pictures, updates view counts, titles, date taken</li>
<li>Download Pictures: downloads pictures from the pictures database meeting certain criteria (currently > 100 views or tagged as "wallpaper")</li>
<li>Process Slides: Adds title and date text to the downloaded pictures</li>
<li>Rebuild Picture Database: deletes the database table and rebuilds it from scratch</li>
<li>Individual pictures can be updated from the admin UI - this goes through the update, download, and process sequence for each picture selected. Typically used after editing the title or date on flickr.</li>
<li>Local version or flickr version of pictures in the database can be viewed from the admin UI</ul>
