from django.contrib import admin
from django.utils.translation import gettext as _

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import (Building, BuildingPlan, PhotoStation, StationImage,
    DisciplineNode)

class BuildingPlanInline(admin.TabularInline):
    model = BuildingPlan
    fields = ('title', 'elev', 'file', 'refresh', 'geometry', 'visible')
    extra = 0

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('title', 'address', )
    inlines = [ BuildingPlanInline,  ]

    fieldsets = (
        (_('Image'), {
            'fields': ('fb_image', ),
        }),
        (None, {
            'fields': ('title', 'date', 'intro', 'address'),
        }),
        (_('Map'), {
            'fields': ('lat', 'long', 'zoom', ),
        }),
        )

class StationImageInline(admin.TabularInline):
    model = StationImage
    fields = ('date', 'fb_image', 'caption', )
    extra = 0

@admin.register(PhotoStation)
class PhotoStationAdmin(admin.ModelAdmin):
    list_display = ( 'title', 'intro', 'build', 'plan', 'lat', 'long')
    list_editable = ( 'lat', 'long')
    inlines = [ StationImageInline,  ]

#@admin.register(Discipline)
#class DisciplineAdmin(admin.ModelAdmin):
    #list_display = ( 'title', 'intro', )

class DisciplineNodeAdmin(TreeAdmin):
    form = movenodeform_factory(DisciplineNode)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'intro'),
        }),
        (None, {
            'fields': ('_position', '_ref_node_id'),
        }),
        )

admin.site.register(DisciplineNode, DisciplineNodeAdmin)
