# Generated by Django 3.1.2 on 2022-01-10 06:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0034_auto_20211210_0907'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='building',
            options={'ordering': ('-date',), 'permissions': [('visit_other_buildings', 'Can visit other buildings')], 'verbose_name': 'Building', 'verbose_name_plural': 'Buildings'},
        ),
    ]
