# buildings
Building management with maps and VR, all in one Django app!
## Overview
Add buildings to your favourite city, add building plans directly from CAD, add building elements and photo stations. Manage plans organizing them in plan sets, do the same with elements adding hyerarchical families. Add data sheets to elements, download them in CSV format. Uses [Leaflet](https://leafletjs.com/) as map engine and [Three](https://threejs.org/) for VR.
## Requirements
This app relies on `GeoDjango`, you will need `PostGis` and extra libraries (see [GeoDjango installation guide](https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/)). Other external packages are [django-filebrowser](https://django-filebrowser.readthedocs.io/en/latest/), [django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/), [django-treebeard](https://django-treebeard.readthedocs.io/en/latest/), [django-colorful](https://pypi.org/project/django-colorful/). For styling [Bootstrap 4](https://getbootstrap.com/) is used. I develop this app inside my personal [starter project](https://github.com/andywar65/project_repo/tree/archi_repo_2) that provides all the libraries you need. If you want to embed `buildings` into your project you will need to make some tweaks. Hope to make the app as portable as possible in future versions.
## Installation
In your project root type `git clone https://github.com/andywar65/buildings`, add `buildings.apps.BuildingsConfig` to `INSTALLED_APPS` and `path(_('buildings/'), include('buildings.urls', namespace = 'buildings'))`, to your project `urls.py`, migrate and collectstatic. You also need to add city settings to `settings.py`:
`CITY_LAT = 41.8988`
`CITY_LONG = 12.5451`
`CITY_ZOOM = 10`
(these are the settings for Rome, change them to your city of choice). These settings provide
initial map defaults. On migration a `Building Manager` group will be created. Users assigned to this group will have full access to building management.
## City
If you have staff permissions, you can also add city settings in `yoursite.com/admin/buildings/city/`. Last city added will be the active one.
## Buildings
With building view permissions, head to `yoursite.com/buildings/`. Here you will interact with a map and a form for adding buildings. Zoom on your building and choose it's location clicking on the map. Carefully choose location (a corner stone is good), because all building plans will be referenced to this point. Complete the form, then click on `Save and continue`. As you can see a marker representing your building is added to the map. Click on the marker, then on the popup title. You will be redirected to the building main page. On the right of the screen you will find buttons to add features to the building: `Plans` and `Plansets` (a way to organize building plans), `Elements` and `Families` (a way to organize building elements) and finally `Photo Stations` (a way to organize pictures). Under the map you will find three other panels, the first listing `Plansets`, the second listing plans belonging to the active plan set, the third with a list of dates (should be empty by now). We will explore these panels further on.
## Plans
Try adding a building plan. A DXF file is requested but not mandatory. DXF is a very popular CAD exchange format. All lines, lwpolylines and circles will be imported in the building plan. Blocks will be transformed in `Elements`. Rotation and origin of the plan must be consistent with map orientation and building location (see above). To import geometries, the `Refresh geometry` checkbox must be active. `Elevation` sets the altitude of the plan, higher plans will hide lower ones. Color of plan geometries will be imported from CAD, along with layer names.
Let's assume that you have saved a building plan and you have staff permissions, head on to `yoursite.com/admin/buildings/plan/` and edit the newly created plan. You will see that all geometries are editable, you can change their colors and the popup message that appears when the geometry is selected on the frontend maps (by default it's the original CAD layer name). WARNING! You will be able to edit only the 2D projection of an object with 3D features (in example a lwpoly rotated in space). 3D data is stored in a hidden JSON field.
## Plan Sets
Go back to your building main page: you will see that the plan does not show up, this is because it must be associated to at least one plan set. When you add a building, a base plan set is created alongside, scroll down to the `Planset` panel and click on the `Modify Planset` button.
