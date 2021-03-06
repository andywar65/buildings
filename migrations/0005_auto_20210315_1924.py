# Generated by Django 3.1.2 on 2021-03-15 18:24

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0004_auto_20210211_1301'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('zoom', models.FloatField(default=10, help_text='Al massimo 23', verbose_name='Fattore di zoom')),
            ],
            options={
                'verbose_name': 'City',
                'verbose_name_plural': 'Cities',
            },
        ),
        migrations.AlterModelOptions(
            name='element',
            options={'ordering': ('build', 'family'), 'verbose_name': 'Elemento', 'verbose_name_plural': 'Elementi'},
        ),
        migrations.AlterModelOptions(
            name='family',
            options={'verbose_name': 'Famiglia di elementi', 'verbose_name_plural': 'Famiglie di elementi'},
        ),
        migrations.AlterField(
            model_name='building',
            name='long',
            field=models.FloatField(default=12.5451, help_text='Coordinate da Google Maps\n            oppure https://openstreetmap.org', verbose_name='Longitudine'),
        ),
        migrations.AlterField(
            model_name='building',
            name='zoom',
            field=models.FloatField(default=10, help_text='Al massimo 23', verbose_name='Fattore di zoom'),
        ),
        migrations.AlterField(
            model_name='element',
            name='family',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='family_element', to='buildings.family', verbose_name='Famiglia'),
        ),
        migrations.AlterField(
            model_name='element',
            name='sheet',
            field=models.JSONField(blank=True, help_text="Un dizionario di caratteristiche dell'elemento", null=True, verbose_name='Foglio dati'),
        ),
        migrations.AlterField(
            model_name='family',
            name='intro',
            field=models.CharField(blank=True, help_text='Poche parole per descrivere la famiglia', max_length=100, null=True, verbose_name='Descrizione'),
        ),
        migrations.AlterField(
            model_name='family',
            name='parent',
            field=models.ForeignKey(help_text='Scegli con attenzione,\n            può essere modificato solo dallo staff in amministrazione', null=True, on_delete=django.db.models.deletion.CASCADE, to='buildings.family', verbose_name='Famiglia genitore'),
        ),
        migrations.AlterField(
            model_name='family',
            name='sheet',
            field=models.JSONField(blank=True, help_text="Un dizionario di caratteristiche dell'elemento", null=True, verbose_name='Foglio dati'),
        ),
        migrations.AlterField(
            model_name='family',
            name='title',
            field=models.CharField(help_text='Nome della famiglia', max_length=50, verbose_name='Titolo'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='visible',
            field=models.BooleanField(default=False, help_text='Spunta se la planimetria è subito visibile', verbose_name='Visibile'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='parent',
            field=models.ForeignKey(help_text='Scegli con attenzione,\n            può essere modificato solo dallo staff in amministrazione', null=True, on_delete=django.db.models.deletion.CASCADE, to='buildings.planset', verbose_name='Set genitore'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='plans',
            field=models.ManyToManyField(blank=True, help_text='Scegli le planimetrie da mostrare nel set', to='buildings.Plan', verbose_name='Planimetrie'),
        ),
    ]
