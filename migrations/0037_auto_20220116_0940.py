# Generated by Django 3.1.2 on 2022-01-16 08:40

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0036_dxfimport_geomjson'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dxfimport',
            name='geom',
            field=django.contrib.gis.db.models.fields.LineStringField(null=True, srid=4326),
        ),
    ]