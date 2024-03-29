from pathlib import Path
from datetime import datetime
from math import radians, sin, cos, fabs, degrees
#asin, acos, degrees, pi, sqrt, pow, fabs, atan2
from geopy.geocoders import Nominatim
import ezdxf
from ezdxf.math import Vec3

from django.db import models, transaction
from django.conf import settings
from django.utils.timezone import now
from django.contrib.sites.models import Site
from django.utils.text import slugify
from django.utils.translation import gettext as _g
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, Polygon, LineString, MultiPolygon
from django.contrib.gis.utils import LayerMapping

from filebrowser.fields import FileBrowseField
from filebrowser.base import FileObject
from treebeard.mp_tree import MP_Node
from colorfield.fields import ColorField
from taggit.managers import TaggableManager

from .map_utils import cad2hex

User = get_user_model()

def get_current_site_name():
    try:
        current_site = Site.objects.get_current()
        return current_site.name
    except Site.DoesNotExist:
        return _("this site")

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
        {'website': get_current_site_name()})

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
    visitor = models.ForeignKey(User, on_delete=models.SET_NULL,
        null=True, verbose_name = _('Building visitor'))

    def __str__(self):
        return self.title

    def get_entry_planset_id(self):
        planset = self.building_planset.get(active=True)
        return planset.id

    def get_base_slug(self):
        return 'base_'+str(self.id)

    def get_normal_path(self):
        return reverse('buildings:building_slug',
            kwargs={'slug': self.slug})

    def get_full_path(self):
        active = self.building_planset.filter(active=True)
        if active:
            set_slug = active.first().slug
        else:
            set_slug = self.get_base_slug()
        return reverse('buildings:building_detail',
            kwargs={'build_slug': self.slug,
            'set_slug': set_slug })

    def image_medium_version_path(self):
        self.fb_image.version_generate("medium")
        return (settings.MEDIA_URL +
            self.fb_image.version_path("medium"))

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

    def get_floor_elevation(self):
        #scale factor
        sc = 6.25
        plan = self.building_plan.all().reverse().first()
        if plan:
            return plan.elev * sc
        else:
            return 0

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = _('Building-%(random)s') % {
                'random': get_random_string(7)}
        if not self.slug:
            self.slug = generate_unique_slug(Building, self.title)
        self.last_updated = now()
        if self.long and self.lat:
            self.location = Point( self.long, self.lat )
            self.long = None
            self.lat = None
        if not self.address:
            geolocator = Nominatim(user_agent=settings.DEFAULT_RECIPIENT)
            loc = geolocator.reverse(str(self.location.coords[1])+","+
                str(self.location.coords[0]))
            if loc.address:
                self.address = loc.address
        if not self.visitor:
            visitor_name = 'visitor-' + get_random_string(7)
            password = User.objects.make_random_password()
            self.visitor = User.objects.create_user(
                username=visitor_name,
                first_name=_('Visitor'),
                last_name=self.title,
                password=make_password(password),
                email=settings.DEFAULT_RECIPIENT)
            group = Group.objects.get(name='Building Guest')
            self.visitor.groups.add(group)
            perm = Permission.objects.get(codename="can_change_profile")
            self.visitor.user_permissions.remove(perm)
            #send message
            subject = _('Building visitor credentials: ') + self.title
            body = _('Password: ') + password
            mailto = [ self.visitor.email, ]
            email = EmailMessage(subject, body, settings.SERVER_EMAIL, mailto)
            email.send()
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
                intro = _("Base plan set"), build=self, active=True)
        try:
            Family.objects.get(slug=self.get_base_slug())
        except:
            Family.add_root(title=self.title, slug=self.get_base_slug(),
                intro = _("Base element family"), build=self,
                sheet = {_g('Building'): self.title})

    class Meta:
        verbose_name = _('Building')
        verbose_name_plural = _('Buildings')
        ordering = ('-date', )
        permissions = [
            ("visit_other_buildings", _("Can visit other buildings")),
        ]

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
    cpg_file = models.FileField(_("CPG file"), max_length=200,
        upload_to="uploads/buildings/plans/shapes/",
        validators=[FileExtensionValidator(allowed_extensions=['cpg', ])],
        null=True, blank=True )
    dbf_file = models.FileField(_("DBF file"), max_length=200,
        upload_to="uploads/buildings/plans/shapes/",
        validators=[FileExtensionValidator(allowed_extensions=['dbf', ])],
        null=True, blank=True )
    prj_file = models.FileField(_("PRJ file"), max_length=200,
        upload_to="uploads/buildings/plans/shapes/",
        validators=[FileExtensionValidator(allowed_extensions=['prj', ])],
        null=True, blank=True )
    shp_file = models.FileField(_("SHP file"), max_length=200,
        upload_to="uploads/buildings/plans/shapes/",
        validators=[FileExtensionValidator(allowed_extensions=['shp', ])],
        null=True, blank=True )
    shx_file = models.FileField(_("SHX file"), max_length=200,
        upload_to="uploads/buildings/plans/shapes/",
        validators=[FileExtensionValidator(allowed_extensions=['shx', ])],
        null=True, blank=True )
    refresh = models.BooleanField(_("Refresh geometry"), default=True)

    def __str__(self):
        return self.title + ' | ' + str(self.elev)

    def map_dictionary(self):
        geometry = []
        return {'id': self.id, 'geometry': geometry,
            'title': self.title, 'elevation': self.elev, }

    @transaction.atomic
    def save_dxf_imports(self, shp_str):
        poly_mapping = {
            #'plan': { 'id': 'plan' },
            'layer': 'layer',
            'olinetype': 'olinetype',
            'color': 'color',
            'width': 'width',
            'thickness': 'thickness',
            'geom': 'LINESTRING25D',
        }
        last = DxfImport.objects.last()
        lm = LayerMapping(DxfImport, shp_str, poly_mapping, transform=True)
        lm.save(strict=True, )
        if last:
            imports = DxfImport.objects.filter(id__gt=last.id)
        else:
            imports = DxfImport.objects.all()
        for imp in imports:
            if imp.geom.closed and imp.geom.simple:
                imp.geometry = Polygon(imp.geom.coords)
            else:
                imp.geometry = imp.geom
            rgb = imp.color.split(',')
            imp.color_field = '#{:02x}{:02x}{:02x}'.format( int(rgb[0]),
                int(rgb[1]), int(rgb[2]) )
            imp.plan = self
            imp.save()

    def transform_vertices(self, geodata, vert):
        trans = []
        transz = []
        gy = 1 / (6371*1000)
        gx = 1 / (6371*1000*fabs(cos(radians(geodata['lat']))))
        for v in vert:
            #normalize to geodata block
            x = geodata['xpos'] - v[0]
            y = geodata['ypos'] - v[1]
            #get true north
            xr = x*cos(geodata['rotation']) - y*sin(geodata['rotation'])
            yr = x*sin(geodata['rotation']) + y*cos(geodata['rotation'])
            #objects are very small with respect to earth, so our transformation
            #from CAD x,y coords to latlong is approximate
            long = geodata['long'] - degrees(xr*gx)
            lat = geodata['lat'] - degrees(yr*gy)
            trans.append((long,lat))
            transz.append((xr,yr,v[2]))
        return trans, transz

    def get_linetype_and_color(self, e, layer_table):
        if e.dxf.linetype == 'BYLAYER':
            linetype = layer_table[e.dxf.layer]['linetype']
        else:
            linetype = e.dxf.linetype
        if e.dxf.color == 256:
            color = layer_table[e.dxf.layer]['color']
        else:
            color = cad2hex(e.dxf.color)
        return linetype, color

    def use_ezdxf(self):
        doc = ezdxf.readfile(Path(settings.MEDIA_ROOT).joinpath(str(self.file)))
        msp = doc.modelspace()
        try:
            #first we look for geodata block
            #(see 'static/buildings/dxf/simple_geodata.dxf')
            blk = msp.query('INSERT[name=="simple_geodata"]').first
            geodata = {
                'lat' : float(blk.get_attrib('LAT').dxf.text),
                'long' : float(blk.get_attrib('LONG').dxf.text),
                'xpos' : blk.dxf.insert[0],
                'ypos' : blk.dxf.insert[1],
                'rotation' : -radians(blk.dxf.rotation)
            }
        except:
            #no geodata found, unable to work on this File
            return
        #prepare layer table
        layer_table = {}
        for layer in doc.layers:
            layer_table[layer.dxf.name] = {
                'color' : cad2hex(layer.color),
                'linetype' : layer.dxf.linetype,
                }
        #start parsing entities
        base_family = Family.objects.get(slug=self.build.get_base_slug())
        for e in msp.query('INSERT'):
            if e.dxf.name == 'simple_geodata':
                continue
            vert, vertz = self.transform_vertices(geodata, [e.dxf.insert])
            sheet = {}
            for at in e.attribs:
                sheet[at.dxf.tag] = at.dxf.text
            try:
                family = Family.objects.get(
                    build_id=self.build.id,
                    title=e.dxf.name
                    )
            except:
                family = base_family.add_child(
                    build=self.build,
                    title=e.dxf.name
                    )
            elm, created = Element.objects.get_or_create(
                build_id=self.build.id,
                family_id=family.id,
                plan_id=self.id,
                defaults={'location': Point(vert[0])},
                )
            if created:
                elm.sheet = sheet
                elm.save()
        for e in msp.query('LINE'):
            points = [e.dxf.start , e.dxf.end]
            vert, vertz = self.transform_vertices(geodata, points)
            geometry = LineString(vert)
            linetype, color = self.get_linetype_and_color(e, layer_table)
            DxfImport.objects.create(
                plan=self,
                layer = e.dxf.layer,
                olinetype = linetype,
                color = e.dxf.color,
                color_field = color,
                width = 0,
                thickness = e.dxf.thickness,
                geom = None,
                geometry = geometry,
                geomjson = {'geodata': geodata, 'vert': vertz, 'type': 'line'}
            )
        for e in msp.query('LWPOLYLINE'):
            vert, vertz = self.transform_vertices(geodata, e.vertices_in_wcs())
            area = ezdxf.math.area(vertz)
            normal=e.ocs().uz
            if not normal[2] == 1:
                try:
                    #first three points may be on same line
                    normal = ezdxf.math.normal_vector_3p(Vec3(vertz[0]),
                        Vec3(vertz[1]), Vec3(vertz[2]))
                except:
                    continue
            if e.is_closed:
                vert.append(vert[0])
                try:
                    #polygon may be "not simple"
                    geometry = Polygon(vert)
                    type = 'polygon'
                except:
                    continue
            else:
                geometry = LineString(vert)
                type = 'polyline'
            width = e.dxf.const_width if e.dxf.const_width else 0
            linetype, color = self.get_linetype_and_color(e, layer_table)
            DxfImport.objects.create(
                plan=self,
                layer = e.dxf.layer,
                olinetype = linetype,
                color = e.dxf.color,
                color_field = color,
                width = width,
                thickness = e.dxf.thickness,
                geom = None,
                geometry = geometry,
                geomjson = {'geodata': geodata, 'vert': vertz, 'type': type,
                    'area': area,
                    'normal': (normal[0],normal[1],normal[2])}
            )
        return

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Plan,
                self.title + ' ' + str(self.elev))
        refresh = True if self.refresh else False
        self.refresh = False
        #upload files
        super(Plan, self).save(*args, **kwargs)
        if refresh and self.file:
            self.use_ezdxf()
        if refresh and self.shp_file:
            #change all shape filenames to same random name
            random = get_random_string(7)
            shapes = "uploads/buildings/plans/shapes/"
            shapes_path = Path(settings.MEDIA_ROOT).joinpath(shapes)
            cpg = Path(settings.MEDIA_ROOT).joinpath(str(self.cpg_file) )
            if cpg.is_file():
                random_cpg = random + '.cpg'
                cpg.replace(shapes_path.joinpath(random_cpg))
                self.cpg_file = shapes + random_cpg
            dbf = Path(settings.MEDIA_ROOT).joinpath(str(self.dbf_file) )
            if dbf.is_file():
                random_dbf = random + '.dbf'
                dbf.replace(shapes_path.joinpath(random_dbf))
                self.dbf_file = shapes + random_dbf
            prj = Path(settings.MEDIA_ROOT).joinpath(str(self.prj_file) )
            if prj.is_file():
                random_prj = random + '.prj'
                prj.replace(shapes_path.joinpath(random_prj))
                self.prj_file = shapes + random_prj
            shp = Path(settings.MEDIA_ROOT).joinpath(str(self.shp_file) )
            if shp.is_file():
                random_shp = random + '.shp'
                shp.replace(shapes_path.joinpath(random_shp))
                self.shp_file = shapes + random_shp
            shx = Path(settings.MEDIA_ROOT).joinpath(str(self.shx_file) )
            if shx.is_file():
                random_shx = random + '.shx'
                shx.replace(shapes_path.joinpath(random_shx))
                self.shx_file = shapes + random_shx
            #update file names
            super(Plan, self).save(*args, **kwargs)
            #prepare data for layer mapping
            shp_path = shapes_path.joinpath(random_shp)
            shp_str = str(shp_path)
            self.save_dxf_imports(shp_str)

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
        through = 'PlanVisibility',
        help_text=_("Choose plans to show in this set") )
    active = models.BooleanField(default=False)

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

    def get_plans_to_serialize(self):
        all_plans, plan_visibility = self.get_self_and_ancestor_plans()
        plans = []
        for plan in all_plans.reverse():
            plan_temp = plan.map_dictionary()
            visibility = plan_visibility[plan]
            plan_temp['visible'] = visibility[1]
            plans.append(plan_temp)
        return plans

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(PlanSet, self.title)
        self.last_updated = now()
        if self.active:
            deactivate = self.build.building_planset.filter(
                active=True).exclude(slug=self.slug)
            deactivate.update(active=False)
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
        {'sitename': get_current_site_name()})

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

    def camera_position(self):
        z = self.plan.elev if self.plan else 0
        data = {
            'lat': self.location.coords[1],
            'long': self.location.coords[0],
            'z': z+1.6 #add eye height
        }
        return data

    def get_floor_elevation(self):
        return self.build.get_floor_elevation()

    def get_building_redirection(self):
        if self.plan:
            return reverse('buildings:plan_detail',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.plan.slug})
        else:
            return self.build.get_full_path()

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

    def get_self_and_descendant_elements(self):
        elements = self.family_element.all()
        descendants = self.get_descendants()
        for descendant in descendants:
            elements |= descendant.family_element.all()
        plan_ids = []
        for element in elements:
            if element.plan:
                plan_ids.append(element.plan.id)
        plans = Plan.objects.filter(id__in=plan_ids).distinct()
        return elements, plans

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
            return self.build.get_full_path()

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
        if not self.intro:
            self.intro = _("No description")
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
    lat = models.FloatField(_("Latitude"), null=True)
    long = models.FloatField(_("Longitude"), null=True,
        help_text=_("""Coordinates from Google Maps
            or https://openstreetmap.org"""))
    location = models.PointField()
    zoom = models.FloatField(_("Zoom factor"), default = settings.CITY_ZOOM,
        help_text=_("Maximum should be 23"))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.long and self.lat:
            self.location = Point( self.long, self.lat )
            self.long = None
            self.lat = None
        super(City, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ("-id", )

def default_intro():
    return (_('Another building log entry by %(name)s!') %
        {'name': get_current_site_name()})

class Journal(models.Model):
    build = models.ForeignKey(Building, on_delete=models.CASCADE,
        related_name='building_journal', verbose_name = _('Building'))
    slug = models.SlugField(max_length=50, editable=False, null=True)
    title = models.CharField(_('Title'),
        help_text=_("The title of the building log entry"),
        max_length = 50)
    intro = models.CharField(_('Introduction'),
        default = default_intro,
        max_length = 100)
    body = models.TextField(_('Text'), null=True)
    date = models.DateField(_('Date'), default = now, )
    last_updated = models.DateTimeField(editable=False, null=True)
    tags = TaggableManager(verbose_name=_("Categories"),
        help_text=_("Comma separated list of categories"),
        blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL,
        blank= True, null=True, verbose_name = _('Author'))

    def get_path(self):
        #temp = self.date
        #conditional added for test to work
        #if isinstance(temp, str):
            #temp = temp.split(' ')[0]
            #temp = datetime.strptime(temp, '%Y-%m-%d')
        #return ( '/' + _g('buildings/') + self.build.slug + '/' + _g('journal/') +
            #temp.strftime("%Y/%m/%d") + '/' + self.slug )
        return reverse('buildings:journal_detail', kwargs={
            'build_slug': self.build.slug,
            'jour_slug': self.slug,
            'year': self.date.year,
            'month': self.date.month,
            'day': self.date.day,})

    def get_previous(self):
        prev = Journal.objects.filter(build=self.build,
            date__lt=self.date).first()
        if prev:
            return prev.get_path()

    def get_next(self):
        next = Journal.objects.filter(build=self.build,
            date__gt=self.date).last()
        if next:
            return next.get_path()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Journal, self.title)
        self.last_updated = now()
        super(Journal, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Building log entry')
        verbose_name_plural = _('Building log entries')
        ordering = ('-date', )

class DxfImport(models.Model):
    plan = models.ForeignKey(Plan, on_delete = models.CASCADE, null=True,
        related_name='plan_dxfimport', verbose_name = _('Plan DXF import'),)
    layer = models.CharField(max_length=254)
    olinetype = models.CharField(max_length=254)
    color = models.CharField(max_length=254)
    color_field = ColorField(default='#FF0000')
    width = models.FloatField()
    thickness = models.FloatField()
    geom = models.LineStringField(srid=4326, null=True)
    geometry = models.GeometryField( verbose_name = _('Geometry'),
        help_text=_("can be LineString or Polygon"), null=True)
    geomjson = models.JSONField( null=True )

    def get_area_or_length(self):
        try:
            area = self.geomjson['area']
            return (_(' Area = %(area)d sqmt') %
                {'area': area})
        except:
            return ''

    class Meta:
        verbose_name = _('DXF Import')
        verbose_name_plural = _('DXF Imports')
