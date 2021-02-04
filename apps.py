from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext as _

def create_buildings_group(sender, **kwargs):
    from django.contrib.auth.models import Permission, Group
    grp, created = Group.objects.get_or_create(name=_('Building Manager'))
    if created:
        permissions = Permission.objects.filter(codename__in=('view_building',
            'add_building', 'change_building', 'delete_building',
            'view_plan', 'add_plan', 'change_plan',
            'delete_plan',
            'view_photostation', 'add_photostation', 'change_photostation',
            'delete_photostation',
            'view_stationimage', 'add_stationimage', 'change_stationimage',
            'delete_stationimage', 'view_discipline', 'add_discipline',
            'change_discipline', 'delete_discipline', 'view_planset',
            'add_planset', 'change_planset',
            'delete_planset',))
        grp.permissions.set(permissions)

def create_plansets(sender, **kwargs):
    from buildings.models import PlanSet
    try:
        PlanSet.objects.get(title=_('Architecture'))
    except:
        PlanSet.add_root(title=_('Architecture'))
    try:
        PlanSet.objects.get(title=_('MEP'))
    except:
        PlanSet.add_root(title=_('MEP'))
    try:
        PlanSet.objects.get(title=_('Structure'))
    except:
        PlanSet.add_root(title=_('Structure'))

class buildingsConfig(AppConfig):
    name = 'buildings'

    def ready(self):
        post_migrate.connect(create_buildings_group, sender=self)
        #post_migrate.connect(create_plansets, sender=self)
