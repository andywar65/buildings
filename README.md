# buildings
Building management with maps and VR, all in one Django app!
## Overview
Add buildings to your favourite city, add building plans directly from CAD, add building elements and photo stations. Manage plans organizing them in plan sets, do the same with elements adding hyerarchical families. Add data sheets to elements, download them in CSV format.
## Requirements
Buildings relies on GeoDjango, you will need PostGis and extra libraries (see GeoDjango installation guide). Other external packages are django-filebrowser, django-crispy-forms, django-treebeard, django-colorful. For styling Bootstrap 4 is used. I develop this app inside a particular project (https://github.com/andywar65/project_repo, archi_repo_2 branch), you will need to make some tweaks to install Buildings inside your project.
## Installation
In your project root type `git clone https://github.com/andywar65/buildings`, add `buildings.apps.BuildingsConfig` to `INSTALLED_APPS` and `path(_('buildings/'), include('buildings.urls', namespace = 'buildings'))`, to your project `urls.py`, migrate and collectstatic. You also need to add city settings to `settings.py`:
`CITY_LAT = 41.8988`
`CITY_LONG = 12.5451`
`CITY_ZOOM = 10`
(above are settings for Rome, change them to your favourite city).
