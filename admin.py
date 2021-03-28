from django.contrib import admin
from django.utils.translation import gettext as _
from django.contrib.gis.admin import OSMGeoAdmin

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import (Building, Plan, PhotoStation, StationImage,
    PlanSet, Family, Element, City)

class PlanInline(admin.TabularInline):
    model = Plan
    fields = ('title', 'elev', 'file', 'refresh', 'geometry', 'visible')
    extra = 0

@admin.register(Building)
class BuildingAdmin(OSMGeoAdmin):
    list_display = ('title', 'address', )
    inlines = [ PlanInline,  ]

    fieldsets = (
        (_('Image'), {
            'fields': ('fb_image', ),
        }),
        (None, {
            'fields': ('title', 'date', 'intro', 'address'),
        }),
        (_('Map'), {
            'fields': ('location', 'zoom', ),
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

class PlanSetAdmin(TreeAdmin):
    form = movenodeform_factory(PlanSet)

    fieldsets = (
        (None, {
            'fields': ('title', 'intro'),
        }),
        (None, {
            'fields': ('_position', '_ref_node_id'),
        }),
        )

admin.site.register(PlanSet, PlanSetAdmin)

class FamilyAdmin(TreeAdmin):
    form = movenodeform_factory(Family)

    fieldsets = (
        (None, {
            'fields': ('title', 'intro', 'sheet'),
        }),
        (None, {
            'fields': ('_position', '_ref_node_id'),
        }),
        )

admin.site.register(Family, FamilyAdmin)

@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'family', 'build', 'plan',)

    fieldsets = (
        (_('Image'), {
            'fields': ('fb_image', ),
        }),
        (None, {
            'fields': ('build', 'family', 'plan', 'intro', 'sheet'),
        }),
        (_('Map'), {
            'fields': ('lat', 'long', ),
        }),
        )

@admin.register(City)
class CityAdmin(OSMGeoAdmin):
    list_display = ('name', 'location')
