# Generated by Django 3.1.2 on 2021-11-09 22:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0026_auto_20211109_2044'),
    ]

    operations = [
        migrations.AddField(
            model_name='dxfimport',
            name='plan',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plan_dxfimport', to='buildings.plan', verbose_name='Plan DXF import'),
        ),
    ]
