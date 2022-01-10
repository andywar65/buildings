from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext as _

def create_buildings_group(sender, **kwargs):
    from django.contrib.auth.models import Permission, Group
    grp, created = Group.objects.get_or_create(name=_('Building Manager'))
    if created:
        permissions = Permission.objects.filter(codename__in=(
            'view_building','add_building','change_building','delete_building',
            'view_plan', 'add_plan', 'change_plan', 'delete_plan',
            'view_photostation', 'add_photostation', 'change_photostation',
            'delete_photostation',
            'view_stationimage', 'add_stationimage', 'change_stationimage',
            'delete_stationimage',
            'view_planset', 'add_planset', 'change_planset', 'delete_planset',
            'view_family', 'add_family', 'change_family', 'delete_family',
            'view_journal', 'add_journal', 'change_journal', 'delete_journal',
            'view_dxfimport', 'add_dxfimport', 'change_dxfimport',
            'delete_dxfimport',
            'view_city', 'add_city', 'change_city',
            'delete_city', 'visit_other_buildings',
            ))
        grp.permissions.set(permissions)
    grp, created = Group.objects.get_or_create(name=_('Building Guest'))
    if created:
        permissions = Permission.objects.filter(codename__in=(
            'view_city',
            'view_building',
            'view_plan',
            'view_photostation',
            'view_stationimage',
            'view_planset',
            'view_family',
            'view_journal',
            'view_dxfimport',
            ))
        grp.permissions.set(permissions)

def create_city(sender, **kwargs):
    from django.contrib.gis.geos import Point
    from buildings.models import City
    city, created = City.objects.get_or_create(name=_('Rome'),
        location=Point( 12.5451, 41.8988 ), zoom=10)

class BuildingsConfig(AppConfig):
    name = 'buildings'

    def ready(self):
        post_migrate.connect(create_buildings_group, sender=self)
        post_migrate.connect(create_city, sender=self)
