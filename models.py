from datetime import datetime

from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.urls import reverse
from django.core.validators import FileExtensionValidator

from filebrowser.fields import FileBrowseField
from filebrowser.base import FileObject
from treebeard.mp_tree import MP_Node

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
    lat = models.FloatField(_("Latitude"), default = settings.CITY_LAT)
    long = models.FloatField(_("Longitude"), default = settings.CITY_LONG,
        help_text=_("""Coordinates from Google Maps
            or https://openstreetmap.org"""))
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
            'path': self.get_full_path(), 'lat': self.lat,
            'long': self.long, 'zoom': self.zoom, 'fb_path': fb_path}

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
    geometry = models.JSONField( null=True, blank=True )
    visible = models.BooleanField(_("Visible"), default=False,
        help_text=_("Check if plan is immediately visible"))

    def __str__(self):
        return self.title + ' | ' + str(self.elev)

    def map_dictionary(self):
        return {'id': self.id, 'geometry': self.geometry,
            'title': self.title, 'visible': self.visible}

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Plan,
                self.title + ' ' + str(self.elev))
        #upload file
        super(Plan, self).save(*args, **kwargs)
        if self.refresh and self.file:
            geometry = workflow(self.file, self.build.lat, self.build.long)
            #this is a sloppy workaround to make working test
            #geometry refreshed
            Plan.objects.filter(id=self.id).update(geometry=geometry,
                refresh=False)

    class Meta:
        verbose_name = _('Building plan')
        verbose_name_plural = _('Building plans')
        ordering = ('-elev', )

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
        help_text=_("Choose plans to show in this set") )

    def __str__(self):
        prefix = ''
        for i in range( self.depth -1 ):
            prefix = prefix + '-'
        return prefix + self.title

    def get_self_and_ancestor_plans(self):
        plans = self.plans.all()
        for ancestor in self.get_ancestors():
            ancestor_plans = ancestor.plans.all()
            plans = plans | ancestor_plans
        return plans.distinct().order_by('elev')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(PlanSet, self.title)
        self.last_updated = now()
        super(PlanSet, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Plan set')
        verbose_name_plural = _('Plan sets')
        ordering = ('build', 'path')

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
            'fb_path': fb_path, 'lat': self.lat, 'long': self.long,
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
        if not self.lat:
            self.lat = self.build.lat
        if not self.long:
            self.long = self.build.long
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

    #def map_dictionary(self):
        #if self.fb_image:
            #self.fb_image.version_generate("medium")
            #fb_path = (settings.MEDIA_URL +
                #self.fb_image.version_path("medium"))
        #else:
            #fb_path = ''
        #path = reverse('buildings:station_detail',
            #kwargs={'build_slug': self.build.slug,
            #'stat_slug': self.slug})
        #return {'id': self.id, 'title': self.title, 'path': path,
            #'fb_path': fb_path, 'lat': self.lat, 'long': self.long,
            #'intro': self.intro, 'plan_id': self.plan_id}

    def save(self, *args, **kwargs):
        if not self.lat:
            self.lat = self.build.lat
        if not self.long:
            self.long = self.build.long
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
