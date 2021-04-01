from datetime import datetime

from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, Polygon, LineString

from filebrowser.fields import FileBrowseField
from filebrowser.base import FileObject
from treebeard.mp_tree import MP_Node
from colorfield.fields import ColorField

from .map_utils import workflow

from django.utils.text import slugify

def generate_unique_slug(klass, field):
    """
    return unique slug if origin slug exists.
    eg: `foo-bar` => `foo-bar-1`

    :param `klass` is Class model.
    :param `field` is specific field for title.
    Thanks to djangosnippets.org!
    """
    origin_slug = slugify(field)
    #slug 'base_' is reserved for PlanSet model
    if klass == PlanSet and origin_slug.startswith('base_'):
        origin_slug = origin_slug.replace('base_', 'bass_')
    unique_slug = origin_slug
    numb = 1
    while klass.objects.filter(slug=unique_slug).exists():
        unique_slug = '%s-%d' % (origin_slug, numb)
        numb += 1
    return unique_slug

def building_default_intro():
    return (_('Another Building by %(website)s!') %
        {'website': settings.WEBSITE_NAME})

def building_default_location():
    city = City.objects.first()
    if city:
        return city.location
    return Point( settings.CITY_LONG, settings.CITY_LAT )

class Building(models.Model):
    slug = models.SlugField(max_length=100, editable=False, null=True)
    image = models.ImageField(_("Image"), max_length=200,
        null=True, blank=True, upload_to='uploads/buildings/images/')
    fb_image = FileBrowseField(_("Image"), max_length=200,
        extensions=[".jpg", ".png", ".jpeg", ".gif", ".tif", ".tiff"],
        null=True, directory='buildings/images/')
    title = models.CharField(_('Title'),
        help_text=_("Building name"),
        max_length = 50, null=True, blank=True)
    intro = models.CharField(_('Introduction'),
        default = building_default_intro,
        help_text = _('Few words to describe this building'),
        max_length = 100)
    date = models.DateField(_('Date'), default = now, )
    last_updated = models.DateTimeField(editable=False, null=True)
    address = models.CharField(_('Address'), null=True, blank=True,
        help_text = _('Something like "Rome - Monteverde" is ok'),
        max_length = 100)
    lat = models.FloatField(_("Latitude"), null=True)
    long = models.FloatField(_("Longitude"), null=True,
        help_text=_("""Coordinates from Google Maps
            or https://openstreetmap.org"""))
    location = models.PointField( srid=4326, null=True,
        default=building_default_location, geography=True)
    zoom = models.FloatField(_("Zoom factor"), default = settings.CITY_ZOOM,
        help_text=_("Maximum should be 23"))

    def __str__(self):
        return self.title

    def get_base_slug(self):
        return 'base_'+str(self.id)

    def get_full_path(self):
        return reverse('buildings:building_detail',
            kwargs={'build_slug': self.slug,
            'set_slug': self.get_base_slug()})

    def map_dictionary(self):
        self.fb_image.version_generate("medium")
        fb_path = (settings.MEDIA_URL +
            self.fb_image.version_path("medium"))
        return {'title': self.title, 'intro': self.intro,
            'path': self.get_full_path(), 'lat': self.location.coords[1],
            'long': self.location.coords[0], 'zoom': self.zoom,
            'fb_path': fb_path}

    def get_planset_annotated_list(self):
        parent = self.building_planset.get(slug=self.get_base_slug())
        return PlanSet.get_annotated_list(parent=parent)

    def get_family_annotated_list(self):
        parent = self.building_family.get(slug=self.get_base_slug())
        return Family.get_annotated_list(parent=parent)

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = _('Building-%(date)s') % {
                'date': self.date.strftime("%d-%m-%y")}
        if not self.slug:
            self.slug = generate_unique_slug(Building, self.title)
        self.last_updated = now()
        if self.long and self.lat:
            self.location = Point( self.long, self.lat )
            self.long = None
            self.lat = None
        super(Building, self).save(*args, **kwargs)
        if self.image:
            #this is a sloppy workaround to make working test
            #image is saved on the front end, passed to fb_image and deleted
            Building.objects.filter(id=self.id).update(image=None,
                fb_image=FileObject(str(self.image)))
        try:
            PlanSet.objects.get(slug=self.get_base_slug())
        except:
            PlanSet.add_root(title=self.title, slug=self.get_base_slug(),
                intro = _("Base plan set"), build=self)
        try:
            Family.objects.get(slug=self.get_base_slug())
        except:
            Family.add_root(title=self.title, slug=self.get_base_slug(),
                intro = _("Base element family"), build=self,
                sheet = {_('Building'): self.title})

    class Meta:
        verbose_name = _('Building')
        verbose_name_plural = _('Buildings')
        ordering = ('-date', )

class Plan(models.Model):

    build = models.ForeignKey(Building, on_delete = models.CASCADE,
        related_name='building_plan', verbose_name = _('Building'))
    title = models.CharField(_('Name'),
        help_text=_("Name of the building plan"), max_length = 50, )
    slug = models.SlugField(max_length=100, editable=False, null=True)
    elev = models.FloatField(_("Elevation in meters"), default = 0)
    file = models.FileField(_("DXF file"), max_length=200,
        upload_to="uploads/buildings/plans/dxf/",
        validators=[FileExtensionValidator(allowed_extensions=['dxf', ])],
        null=True, blank=True )
    refresh = models.BooleanField(_("Refresh geometry"), default=True)

    def __str__(self):
        return self.title + ' | ' + str(self.elev)

    def map_dictionary(self):
        geometry = []
        for gm in self.plan_geometry.all():
            gmd = {}
            if gm.geometry.geom_typeid == 1:
                gmd['type'] = 'polyline'
            else:
                gmd['type'] = 'polygon'
                gmc=gm.geometry.coords[0]
            gmd['coords'] = []
            for crd in gmc:
                gmd['coords'].append([crd[1], crd[0]])
            gmd['color'] = gm.color
            gmd['popup'] = gm.popup
            geometry.append(gmd)
        return {'id': self.id, 'geometry': geometry,
            'title': self.title, }

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Plan,
                self.title + ' ' + str(self.elev))
        #upload file
        super(Plan, self).save(*args, **kwargs)
        if self.refresh and self.file:
            #clear plan geometries
            self.plan_geometry.all().delete()
            geometry, elements = workflow(self.file,
                self.build.location.coords[1],
                self.build.location.coords[0])
            for gm in geometry:
                if gm['type'] == 'polygon':
                    PlanGeometry.objects.create(plan_id=self.id,
                        color=gm['color'],
                        popup=gm['popup'],
                        geometry=Polygon(gm['coords']))
                elif gm['type'] == 'linestring':
                    PlanGeometry.objects.create(plan_id=self.id,
                        color=gm['color'],
                        popup=gm['popup'],
                        geometry=LineString(gm['coords']))
            #this is a sloppy workaround to make working test
            #geometry refreshed
            Plan.objects.filter(id=self.id).update(refresh=False)
            base_family = Family.objects.get(slug=self.build.get_base_slug())
            for element in elements:
                try:
                    family = Family.objects.get(
                        build_id=self.build.id,
                        title=element['family']
                        )
                except:
                    family = base_family.add_child(
                        build=self.build,
                        title=element['family']
                        )
                elm, created = Element.objects.get_or_create(
                    build_id=self.build.id,
                    family_id=family.id,
                    plan_id=self.id,
                    defaults={'location': Point(element['coords'][1],
                        element['coords'][0])},
                    )
                if created:
                    elm.sheet = element['sheet']
                    elm.save()

    class Meta:
        verbose_name = _('Building plan')
        verbose_name_plural = _('Building plans')
        ordering = ('-elev', )

class PlanGeometry(models.Model):
    plan = models.ForeignKey(Plan, on_delete = models.CASCADE,
        related_name='plan_geometry', verbose_name = _('Plan geometry'),)
    color = ColorField(default='#FF0000')
    popup = models.CharField(_('Popup'),
        help_text=_("Geometry description in popup"), max_length = 100, )
    geometry = models.GeometryField( verbose_name = _('Geometry'),
        help_text=_("can be LineString or Polygon"))

    def __str__(self):
        return self.plan.title + '-' + str(self.id)

    class Meta:
        verbose_name = _('Plan geometry')
        verbose_name_plural = _('Plan geometries')

class PlanSet(MP_Node):
    build = models.ForeignKey(Building, on_delete = models.CASCADE,
        related_name='building_planset', verbose_name = _('Building'))
    parent = models.ForeignKey('self', verbose_name = _('Parent set'),
        null=True, on_delete = models.CASCADE,
        help_text = _("""Choose carefully,
            can be changed only by staff in admin"""),
        )
    title = models.CharField(_('Title'),
        help_text=_("Set name"),
        max_length = 50, )
    intro = models.CharField(_('Description'),
        null=True, blank=True,
        help_text = _('Few words to describe the set'),
        max_length = 100)
    slug = models.SlugField(max_length=100, editable=False, null=True)
    plans = models.ManyToManyField(Plan,
        blank = True, verbose_name = _('Plans'),
        through = 'PlanVisibility',
        help_text=_("Choose plans to show in this set") )

    def __str__(self):
        prefix = ''
        for i in range( self.depth -1 ):
            prefix = prefix + '-'
        return prefix + self.title

    def get_self_and_ancestor_plans(self):
        plan_visibility = {}
        plans = self.plans.all()#first plan queryset
        for ancestor in self.get_ancestors():#get planset ancestors
            ancestor_plans = ancestor.plans.all()#get their plans
            plans = plans | ancestor_plans#merge querysets
            for ancestor_plan in ancestor_plans:#set visibility for ancestors
                pv = PlanVisibility.objects.get(set_id=ancestor.id,
                    plan_id=ancestor_plan.id)
                plan_visibility[ancestor_plan] = ( pv.id, pv.visibility )
        plans = plans.distinct().order_by('elev')#squash duplicates

        for plan in self.plans.all():#repeat queryset for active planset
            #eventually override ancestor visibility
            pv = PlanVisibility.objects.get(set_id=self.id,
                plan_id=plan.id)
            plan_visibility[plan] = ( pv.id, pv.visibility )
        return plans, plan_visibility

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(PlanSet, self.title)
        self.last_updated = now()
        super(PlanSet, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Plan set')
        verbose_name_plural = _('Plan sets')
        ordering = ('build', 'path')

class PlanVisibility(models.Model):
    plan = models.ForeignKey(Plan, on_delete = models.CASCADE,
        related_name='plan_visibility', verbose_name = _('Building plan'))
    set = models.ForeignKey(PlanSet, on_delete = models.CASCADE,
        related_name='planset_visibility', verbose_name = _('Plan set'))
    visibility = models.BooleanField(_("Visible"), default=True,
        help_text=_("Check if plan is visible in this plan set"))

    class Meta:
        verbose_name = _('Plan visibility')

def photo_station_default_intro():
    return (_('Another photo station by %(sitename)s!') %
        {'sitename': settings.WEBSITE_NAME})

class PhotoStation(models.Model):

    build = models.ForeignKey(Building, on_delete = models.CASCADE,
        related_name='building_station', verbose_name = _('Building'))
    plan = models.ForeignKey(Plan, on_delete = models.SET_NULL,
        related_name='plan_station', verbose_name = _('Building plan'),
        null=True, blank=True)
    title = models.CharField(_('Title'),
        help_text=_("Title of the photo station"), max_length = 50, )
    slug = models.SlugField(max_length=100, editable=False, null=True)
    intro = models.CharField(_('Description'),
        default = photo_station_default_intro,
        max_length = 100)
    lat = models.FloatField(_("Latitude"), null=True, blank=True)
    long = models.FloatField(_("Longitude"), null=True, blank=True)
    location = models.PointField( srid=4326, null=True, blank=True,
        geography=True )

    def __str__(self):
        return self.title + ' / ' + self.build.title

    def map_dictionary(self):
        if self.station_image.first():
            self.station_image.first().fb_image.version_generate("medium")
            fb_path = (settings.MEDIA_URL +
                self.station_image.first().fb_image.version_path("medium"))
        else:
            fb_path = ''
        path = reverse('buildings:station_detail',
            kwargs={'build_slug': self.build.slug,
            'stat_slug': self.slug})
        return {'id': self.id, 'title': self.title, 'path': path,
            'fb_path': fb_path, 'lat': self.location.coords[1],
            'long': self.location.coords[0],
            'intro': self.intro, 'plan_id': self.plan_id}

    def get_building_redirection(self):
        if self.plan:
            return reverse('buildings:plan_detail',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.plan.slug})
        else:
            return reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.build.get_base_slug()})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(PhotoStation, self.title)
        if self.lat and self.long:
            self.location = Point( self.long, self.lat )
            self.long = None
            self.lat = None
        if not self.location:
            self.location = self.build.location
        super(PhotoStation, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Photo station')
        verbose_name_plural = _('Photo stations')
        ordering = ('build', 'title')

class StationImage(models.Model):
    stat = models.ForeignKey(PhotoStation, null=True,
        on_delete = models.CASCADE, related_name='station_image',
        verbose_name = _('Station'))
    date = models.DateTimeField(_('Date:'), default = now, )
    image = models.ImageField(_("Image"), max_length=200,
        null=True, blank=True, upload_to='uploads/buildings/images/')
    fb_image = FileBrowseField(_("Image"), max_length=200,
        extensions=[".jpg", ".png", ".jpeg", ".gif", ".tif", ".tiff"],
        null=True, directory='buildings/images/')
    caption = models.CharField(_("Caption"), max_length = 200, blank=True,
        null=True)

    def save(self, *args, **kwargs):
        #save and upload image
        super(StationImage, self).save(*args, **kwargs)
        if self.image:
            #this is a sloppy workaround to make working test
            #image is saved on the front end, passed to fb_image and deleted
            StationImage.objects.filter(id=self.id).update(image=None,
                fb_image=FileObject(str(self.image)))

    class Meta:
        verbose_name=_("Image")
        verbose_name_plural=_("Images")
        ordering = ('-date', )

class Family(MP_Node):
    build = models.ForeignKey(Building, on_delete = models.CASCADE,
        related_name='building_family', verbose_name = _('Building'))
    parent = models.ForeignKey('self', verbose_name = _('Parent family'),
        null=True,
        help_text = _("""Choose carefully,
            can be changed only by staff in admin"""),
        on_delete = models.CASCADE)
    title = models.CharField(_('Title'),
        help_text=_("Family name"),
        max_length = 50, )
    intro = models.CharField(_('Description'),
        null=True, blank=True,
        help_text = _('Few words to describe the family'),
        max_length = 100)
    slug = models.SlugField(max_length=100, editable=False, null=True)
    sheet = models.JSONField(_('Data sheet'), null=True, blank=True,
        help_text=_("A dictionary of element features") )

    def __str__(self):
        prefix = ''
        for i in range( self.depth -1 ):
            prefix = prefix + '-'
        return prefix + self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Family, self.title)
        super(Family, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Element Family')
        verbose_name_plural = _('Element Families')

class Element(models.Model):

    build = models.ForeignKey(Building, on_delete = models.CASCADE,
        related_name='building_element', verbose_name = _('Building'))
    plan = models.ForeignKey(Plan, on_delete = models.SET_NULL,
        related_name='plan_element', verbose_name = _('Building plan'),
        null=True, blank=True)
    family = models.ForeignKey(Family, on_delete = models.CASCADE,
        related_name='family_element', verbose_name = _('Family'),)
    image = models.ImageField(_("Image"), max_length=200,
        null=True, blank=True, upload_to='uploads/buildings/images/')
    fb_image = FileBrowseField(_("Image"), max_length=200,
        extensions=[".jpg", ".png", ".jpeg", ".gif", ".tif", ".tiff"],
        null=True, directory='buildings/images/')
    intro = models.CharField(_('Description'),
        null=True, blank=True, max_length = 200)
    lat = models.FloatField(_("Latitude"), null=True, blank=True)
    long = models.FloatField(_("Longitude"), null=True, blank=True)
    location = models.PointField(srid=4326, null=True, geography=True )
    sheet = models.JSONField(_('Data sheet'), null=True, blank=True,
        help_text=_("A dictionary of element features") )

    def __str__(self):
        return self.family.title + '-' + str(self.id)

    def get_building_redirection(self):
        if self.plan:
            return reverse('buildings:plan_detail',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.plan.slug})
        else:
            return reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.build.get_base_slug()})

    def map_dictionary(self):
        if self.fb_image is not None:
            self.fb_image.version_generate("medium")
            fb_path = (settings.MEDIA_URL +
                self.fb_image.version_path("medium"))
        else:
            fb_path = ''
        path = reverse('buildings:element_change',
            kwargs={'slug': self.build.slug,
            'pk': self.id})
        return {'id': self.id, 'title': self.__str__(), 'path': path,
            'fb_path': fb_path, 'lat': self.location.coords[1],
            'long': self.location.coords[0],
            'intro': self.intro, 'plan_id': self.plan_id,
            'sheet': self.sheet}

    def save(self, *args, **kwargs):
        if self.lat and self.long:
            self.location = Point( self.long, self.lat )
            self.long = None
            self.lat = None
        if not self.location:
            self.location = self.build.location
        sheet = {}
        for ancestor in self.family.get_ancestors():
            if isinstance(ancestor.sheet, dict):
                for key, value in ancestor.sheet.items():
                    sheet[ key ] = value
        if isinstance(self.family.sheet, dict):
            for key, value in self.family.sheet.items():
                sheet[ key ] = value
        if isinstance(self.sheet, dict):
            for key, value in self.sheet.items():
                sheet[ key ] = value
        self.sheet = sheet
        super(Element, self).save(*args, **kwargs)
        if self.image:
            #this is a sloppy workaround to make working test
            #image is saved on the front end, passed to fb_image and deleted
            Element.objects.filter(id=self.id).update(image=None,
                fb_image=FileObject(str(self.image)))

    class Meta:
        verbose_name = _('Element')
        verbose_name_plural = _('Elements')
        ordering = ('build', 'family')

class City(models.Model):
    name = models.CharField(max_length=100)
    location = models.PointField()
    zoom = models.FloatField(_("Zoom factor"), default = settings.CITY_ZOOM,
        help_text=_("Maximum should be 23"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
