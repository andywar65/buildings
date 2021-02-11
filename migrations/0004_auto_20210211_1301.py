# Generated by Django 3.1.2 on 2021-02-11 12:01

from django.db import migrations, models
import django.db.models.deletion
import filebrowser.fields


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0003_auto_20210210_0014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='building',
            name='long',
            field=models.FloatField(default=12.5451, help_text='Coordinates from Google Maps\n            or https://openstreetmap.org', verbose_name='Longitudine'),
        ),
        migrations.AlterField(
            model_name='family',
            name='parent',
            field=models.ForeignKey(help_text='Choose carefully,\n            can be changed only by staff in admin', null=True, on_delete=django.db.models.deletion.CASCADE, to='buildings.family', verbose_name='Parent family'),
        ),
        migrations.AlterField(
            model_name='planset',
            name='parent',
            field=models.ForeignKey(help_text='Choose carefully,\n            can be changed only by staff in admin', null=True, on_delete=django.db.models.deletion.CASCADE, to='buildings.planset', verbose_name='Set genitore'),
        ),
        migrations.CreateModel(
            name='Element',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, max_length=200, null=True, upload_to='uploads/buildings/images/', verbose_name='Immagine')),
                ('fb_image', filebrowser.fields.FileBrowseField(max_length=200, null=True, verbose_name='Immagine')),
                ('intro', models.CharField(blank=True, max_length=200, null=True, verbose_name='Descrizione')),
                ('lat', models.FloatField(blank=True, null=True, verbose_name='Latitudine')),
                ('long', models.FloatField(blank=True, null=True, verbose_name='Longitudine')),
                ('sheet', models.JSONField(blank=True, help_text='A dictionary of element features', null=True, verbose_name='Data sheet')),
                ('build', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='building_element', to='buildings.building', verbose_name='Edificio')),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='family_element', to='buildings.family', verbose_name='Family')),
                ('plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='plan_element', to='buildings.plan', verbose_name='Planimetria')),
            ],
            options={
                'verbose_name': 'Element',
                'verbose_name_plural': 'Elements',
                'ordering': ('build', 'family'),
            },
        ),
    ]
