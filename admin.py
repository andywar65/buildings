from django.contrib import admin
from django.utils.translation import gettext as _
#from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.gis.forms.widgets import OSMWidget
from django.contrib.gis.db import models

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import (Building, Plan, PhotoStation, StationImage,
    PlanSet, Family, Element, City, PlanGeometry, Journal, Comuni)

class PlanInline(admin.TabularInline):
    model = Plan
    fields = ('title', 'elev', 'file', 'refresh', )
    extra = 0

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('title', 'address', )
    inlines = [ PlanInline,  ]
    formfield_overrides = {
        models.PointField: {"widget": OSMWidget},
    }

    fieldsets = (
        (_('Image'), {
            'fields': ('fb_image', ),
        }),
        (None, {
            'fields': ('title', 'date', 'intro', 'address', 'private'),
        }),
        (_('Map'), {
            'fields': ('location', 'zoom', ),
        }),
        )

class PlanGeometryInline(admin.TabularInline):
    model = PlanGeometry
    fields = ('geometry', 'color', 'popup', )
    extra = 0
    formfield_overrides = {
        models.GeometryField: {"widget": OSMWidget},
    }

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'build', 'elev', 'file')
    inlines = [ PlanGeometryInline,  ]

    fieldsets = (
        (None, {
            'fields': ('title', 'build', 'elev', ),
        }),
        (_('File'), {
            'fields': ('file', 'refresh', ),
        }),
        )

@admin.register(Comuni)
class ComuniAdmin(admin.ModelAdmin):
    list_display = ('comune_com', )
    formfield_overrides = {
        models.GeometryField: {"widget": OSMWidget},
    }

#@admin.register(PlanGeometry)
#class PlanGeometryAdmin(OSMGeoAdmin):
    #list_display = ('id', 'plan', )
    #fieldsets = (
        #(None, {
            #'fields': ('plan', 'color', 'popup', ),
        #}),
        #(_('Geometry'), {
            #'fields': ('geometry', ),
        #}),
        #)

class StationImageInline(admin.TabularInline):
    model = StationImage
    fields = ('date', 'fb_image', 'caption', )
    extra = 0

@admin.register(PhotoStation)
class PhotoStationAdmin(admin.ModelAdmin):
    list_display = ( 'title', 'intro', 'build', 'plan', 'location')
    inlines = [ StationImageInline,  ]
    formfield_overrides = {
        models.PointField: {"widget": OSMWidget},
    }
    fieldsets = (
        (_('Building'), {
            'fields': ('build', 'plan' ),
        }),
        (None, {
            'fields': ('title', 'intro', ),
        }),
        (_('Map'), {
            'fields': ('location', ),
        }),
        )

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
    list_display = ( 'id', 'family', 'build', 'plan', 'location')
    formfield_overrides = {
        models.PointField: {"widget": OSMWidget},
    }

    fieldsets = (
        (_('Image'), {
            'fields': ('fb_image', ),
        }),
        (None, {
            'fields': ('build', 'family', 'plan', 'intro', 'sheet'),
        }),
        (_('Map'), {
            'fields': ('location', ),
        }),
        )

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    formfield_overrides = {
        models.PointField: {"widget": OSMWidget},
    }

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('build', 'title', 'date', )
    search_fields = ('title', 'date', 'intro', )

    class Media:
        js = [
            '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
            '/static/js/tinymce_setup.js',
        ]

    fieldsets = (
        (None, {
            'fields': ('build', 'title', 'date', 'intro'),
        }),
        ('Testo', {
            'classes': ('grp-collapse', ),
            'fields': ('body', ),
        }),
        (None, {
            'fields': ('tags', 'author' ),
        }),
        )
