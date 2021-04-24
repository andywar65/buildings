# Generated by Django 3.1.2 on 2021-04-19 16:10

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0016_auto_20210414_2325'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='plangeometry',
            options={'verbose_name': 'Geometria della planimetria', 'verbose_name_plural': 'Geometrie della planimetria'},
        ),
        migrations.RemoveField(
            model_name='plangeometry',
            name='geometryz',
        ),
        migrations.AddField(
            model_name='plangeometry',
            name='geomjson',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='geometry',
            field=django.contrib.gis.db.models.fields.GeometryField(help_text='può essere LineString o Polygon', srid=4326, verbose_name='Geometria'),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='is3d',
            field=models.BooleanField(default=False, help_text='Usa la terza dimensione nella vista in soggettiva', verbose_name="E' 3D"),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_geometry', to='buildings.plan', verbose_name='Geometria della planimetria'),
        ),
        migrations.AlterField(
            model_name='plangeometry',
            name='popup',
            field=models.CharField(help_text='Descrizione della geometria nel popup', max_length=100, verbose_name='Popup'),
        ),
    ]