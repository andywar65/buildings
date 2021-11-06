# Generated by Django 3.1.2 on 2021-11-06 22:58

import buildings.models
from django.conf import settings
import django.contrib.gis.db.models.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import filebrowser.fields
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('buildings', '0024_delete_comuni'),
    ]

    operations = [
        migrations.CreateModel(
            name='DxfImport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('layer', models.CharField(max_length=254)),
                ('olinetype', models.CharField(max_length=254)),
                ('color', models.CharField(max_length=254)),
                ('width', models.FloatField()),
                ('thickness', models.FloatField()),
                ('geom', django.contrib.gis.db.models.fields.LineStringField(srid=4326)),
            ],
            options={
                'verbose_name': 'DXF Import',
                'verbose_name_plural': 'DXF Imports',
            },
        ),
        migrations.AlterModelOptions(
            name='building',
            options={'ordering': ('-date',), 'verbose_name': 'Building', 'verbose_name_plural': 'Buildings'},
        ),
        migrations.AlterModelOptions(
            name='city',
            options={'verbose_name': 'City', 'verbose_name_plural': 'Cities'},
        ),
        migrations.AlterModelOptions(
            name='element',
            options={'ordering': ('build', 'family'), 'verbose_name': 'Element', 'verbose_name_plural': 'Elements'},
        ),
        migrations.AlterModelOptions(
            name='family',
            options={'verbose_name': 'Element Family', 'verbose_name_plural': 'Element Families'},
        ),
        migrations.AlterModelOptions(
            name='journal',
            options={'ordering': ('-date',), 'verbose_name': 'Building log entry', 'verbose_name_plural': 'Building log entries'},
        ),
        migrations.AlterModelOptions(
            name='photostation',
            options={'ordering': ('build', 'title'), 'verbose_name': 'Photo station', 'verbose_name_plural': 'Photo stations'},
        ),
        migrations.AlterModelOptions(
            name='plan',
            options={'ordering': ('-elev',), 'verbose_name': 'Building plan', 'verbose_name_plural': 'Building plans'},
        ),
        migrations.AlterModelOptions(
            name='plangeometry',
            options={'verbose_name': 'Plan geometry', 'verbose_name_plural': 'Plan geometries'},
        ),
        migrations.AlterModelOptions(
            name='planset',
            options={'ordering': ('build', 'path'), 'verbose_name': 'Plan set', 'verbose_name_plural': 'Plan sets'},
        ),
        migrations.AlterModelOptions(
            name='planvisibility',
            options={'verbose_name': 'Plan visibility'},
        ),
        migrations.AlterModelOptions(
            name='stationimage',
            options={'ordering': ('-date',), 'verbose_name': 'Image', 'verbose_name_plural': 'Images'},
        ),
        migrations.AlterField(
            model_name='building',
            name='address',
            field=models.CharField(blank=True, help_text='Something like "Rome - Monteverde" is ok', max_length=100, null=True, verbose_name='Address'),
        ),
        migrations.AlterField(
            model_name='building',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='building',
            name='fb_image',
            field=filebrowser.fields.FileBrowseField(max_length=200, null=True, verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='building',
            name='image',
            field=models.ImageField(blank=True, max_length=200, null=True, upload_to='uploads/buildings/images/', verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='building',
            name='intro',
            field=models.CharField(default=buildings.models.building_default_intro, help_text='Few words to describe this building', max_length=100, verbose_name='Introduction'),
        ),
        migrations.AlterField(
            model_name='building',
            name='lat',
            field=models.FloatField(null=True, verbose_name='Latitude'),
        ),
        migrations.AlterField(
            model_name='building',
            name='long',
            field=models.FloatField(help_text='Coordinates from Google Maps\n            or https://openstreetmap.org', null=True, verbose_name='Longitude'),
        ),
        migrations.AlterField(
            model_name='building',
            name='private',
            field=models.BooleanField(default=True, help_text='Can be viewed only by authenticated users', verbose_name='Private'),
        ),
        migrations.AlterField(
            model_name='building',
            name='title',
            field=models.CharField(blank=True, help_text='Building name', max_length=50, null=True, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='building',
            name='zoom',
            field=models.FloatField(default=10, help_text='Maximum should be 23', verbose_name='Zoom factor'),
        ),
        migrations.AlterField(
            model_name='city',
            name='zoom',
            field=models.FloatField(default=10, help_text='Maximum should be 23', verbose_name='Zoom factor'),
        ),
        migrations.AlterField(
            model_name='element',
            name='build',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='building_element', to='buildings.building', verbose_name='Building'),
        ),
        migrations.AlterField(
            model_name='element',
            name='family',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='family_element', to='buildings.family', verbose_name='Family'),
        ),
        migrations.AlterField(
            model_name='element',
            name='fb_image',
            field=filebrowser.fields.FileBrowseField(max_length=200, null=True, verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='element',
            name='image',
            field=models.ImageField(blank=True, max_length=200, null=True, upload_to='uploads/buildings/images/', verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='element',
            name='intro',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='element',
            name='lat',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitude'),
        ),
        migrations.AlterField(
            model_name='element',
            name='long',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitude'),
        ),
        migrations.AlterField(
            model_name='element',
            name='plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='plan_element', to='buildings.plan', verbose_name='Building plan'),
        ),
        migrations.AlterField(
            model_name='element',
            name='sheet',
            field=models.JSONField(blank=True, help_text='A dictionary of element features', null=True, verbose_name='Data sheet'),
        ),
        migrations.AlterField(
            model_name='family',
            name='build',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='building_family', to='buildings.building', verbose_name='Building'),
        ),
        migrations.AlterField(
            model_name='family',
            name='intro',
            field=models.CharField(blank=True, help_text='Few words to describe the family', max_length=100, null=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='family',
            name='parent',
            field=models.ForeignKey(help_text='Choose carefully,\n            can be changed only by staff in admin', null=True, on_delete=django.db.models.deletion.CASCADE, to='buildings.family', verbose_name='Parent family'),
        ),
        migrations.AlterField(
            model_name='family',
            name='sheet',
            field=models.JSONField(blank=True, help_text='A dictionary of element features', null=True, verbose_name='Data sheet'),
        ),
        migrations.AlterField(
            model_name='family',
            name='title',
            field=models.CharField(help_text='Family name', max_length=50, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Author'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='body',
            field=models.TextField(null=True, verbose_name='Text'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='build',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='building_journal', to='buildings.building', verbose_name='Building'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='intro',
            field=models.CharField(default=buildings.models.default_intro, max_length=100, verbose_name='Introduction'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='Comma separated list of categories', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Categories'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='title',
            field=models.CharField(help_text='The title of the building log entry', max_length=50, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='photostation',
            name='build',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='building_station', to='buildings.building', verbose_name='Building'),
        ),
        migrations.AlterField(
            model_name='photostation',
            name='intro',
            field=models.CharField(default=buildings.models.photo_station_default_intro, max_length=100, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='photostation',
            name='lat',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitude'),
        ),
        migrations.AlterField(
            model_name='photostation',
            name='long',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitude'),
        ),
        migrations.AlterField(
            model_name='photostation',
            name='plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='plan_station', to='buildings.plan', verbose_name='Building plan'),
        ),
        migrations.AlterField(
            model_name='photostation',
            name='title',
            field=models.CharField(help_text='Title of the photo station', max_length=50, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='build',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='building_plan', to='buildings.building', verbose_name='Building'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='elev',
            field=models.FloatField(default=0, verbose_name='Elevation in meters'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='file',
            field=models.FileField(blank=True, max_length=200, null=True, upload_to='uploads/buildings/plans/dxf/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['dxf'])], verbose_name='DXF file'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='refresh',
            field=models.BooleanField(default=True, verbose_name='Refresh geometry'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='title',
            field=models.CharField(help_text='Name of the building plan', max_length=50, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='geometry',
            field=django.contrib.gis.db.models.fields.GeometryField(help_text='can be LineString or Polygon', srid=4326, verbose_name='Geometry'),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='is3d',
            field=models.BooleanField(default=False, help_text='Use third dimension in camera view', verbose_name='Is 3D'),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_geometry', to='buildings.plan', verbose_name='Plan geometry'),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='popup',
            field=models.CharField(help_text='Geometry description in popup', max_length=100, verbose_name='Popup'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='build',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='building_planset', to='buildings.building', verbose_name='Building'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='intro',
            field=models.CharField(blank=True, help_text='Few words to describe the set', max_length=100, null=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='parent',
            field=models.ForeignKey(help_text='Choose carefully,\n            can be changed only by staff in admin', null=True, on_delete=django.db.models.deletion.CASCADE, to='buildings.planset', verbose_name='Parent set'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='plans',
            field=models.ManyToManyField(blank=True, help_text='Choose plans to show in this set', through='buildings.PlanVisibility', to='buildings.Plan', verbose_name='Plans'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='title',
            field=models.CharField(help_text='Set name', max_length=50, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='planvisibility',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_visibility', to='buildings.plan', verbose_name='Building plan'),
        ),
        migrations.AlterField(
            model_name='planvisibility',
            name='set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planset_visibility', to='buildings.planset', verbose_name='Plan set'),
        ),
        migrations.AlterField(
            model_name='planvisibility',
            name='visibility',
            field=models.BooleanField(default=True, help_text='Check if plan is visible in this plan set', verbose_name='Visible'),
        ),
        migrations.AlterField(
            model_name='stationimage',
            name='caption',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Caption'),
        ),
        migrations.AlterField(
            model_name='stationimage',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date:'),
        ),
        migrations.AlterField(
            model_name='stationimage',
            name='fb_image',
            field=filebrowser.fields.FileBrowseField(max_length=200, null=True, verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='stationimage',
            name='image',
            field=models.ImageField(blank=True, max_length=200, null=True, upload_to='uploads/buildings/images/', verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='stationimage',
            name='stat',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='station_image', to='buildings.photostation', verbose_name='Station'),
        ),
    ]
