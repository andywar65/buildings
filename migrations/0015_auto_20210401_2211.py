# Generated by Django 3.1.2 on 2021-04-01 20:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0014_auto_20210331_1754'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plan',
            name='geometry',
        ),
        migrations.RemoveField(
            model_name='plan',
            name='visible',
        ),
    ]
