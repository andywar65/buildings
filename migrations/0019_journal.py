# Generated by Django 3.1.2 on 2021-06-23 21:22

import buildings.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('buildings', '0018_building_private'),
    ]

    operations = [
        migrations.CreateModel(
            name='Journal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(editable=False, null=True)),
                ('title', models.CharField(help_text='The title of the building log entry', max_length=50, verbose_name='Titolo')),
                ('intro', models.CharField(default=buildings.models.default_intro, max_length=100, verbose_name='Introduzione')),
                ('body', models.TextField(null=True, verbose_name='Testo')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Data')),
                ('last_updated', models.DateTimeField(editable=False, null=True)),
                ('build', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buildings.building', verbose_name='Edificio')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='Lista di categorie separate da virgole', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Categorie')),
            ],
            options={
                'verbose_name': 'Building log entry',
                'verbose_name_plural': 'Building log entries',
                'ordering': ('-date',),
            },
        ),
    ]
