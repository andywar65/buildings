from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
    FormView, TemplateView)
from django.views.generic.dates import YearArchiveView, DayArchiveView
from django.utils.crypto import get_random_string
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext as _

from buildings.models import Building, Plan, PhotoStation, StationImage
from buildings.forms import ( PhotoStationCreateForm,
    BuildingDeleteForm, StationImageCreateForm, StationImageUpdateForm, )
from buildings.views.building import (VisitorPermReqMix, VisitorPassTestMix,
    AlertMixin)

class PhotoStationCreateView( VisitorPermReqMix, VisitorPassTestMix, AlertMixin,
    CreateView ):
    model = PhotoStation
    permission_required = 'buildings.add_photostation'
    form_class = PhotoStationCreateForm

    def setup(self, request, *args, **kwargs):
        super(PhotoStationCreateView, self).setup(request, *args, **kwargs)
        #here we get the building by the slug
        self.build = get_object_or_404( Building, slug = self.kwargs['slug'] )

    def get_initial(self):
        initial = super( PhotoStationCreateView, self ).get_initial()
        initial['build'] = self.build.id
        initial['lat'] = self.build.location.coords[1]
        initial['long'] = self.build.location.coords[0]
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_alerts_to_context(context)
        context['build'] = self.build
        #we add the following to feed the map
        #building data
        build = self.build.map_dictionary()
        #plan data
        plans = []
        for plan in self.build.building_plan.all().reverse():
            plan_dict = plan.map_dictionary()
            plan_dict['visible'] = False
            plans.append(plan_dict)
        context['map_data'] = {
            'build': build,
            'plans': plans,
            'on_map_click': True,
            'no_plan_popup': True,
            'mapbox_token': settings.MAPBOX_TOKEN
            }

        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:station_create',
                kwargs={'slug': self.build.slug}) +
                f'?created={self.object.title}&model={_("Photo station")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:station_change',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.object.slug }) +
                f'?created={self.object.title}&model={_("Photo station")}')
        else:
            return (reverse('buildings:station_detail',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.object.slug }) +
                f'?created={self.object.title}&model={_("Photo station")}')

class PhotoStationUpdateView( VisitorPermReqMix, VisitorPassTestMix, AlertMixin,
    UpdateView ):
    model = PhotoStation
    permission_required = 'buildings.change_photostation'
    form_class = PhotoStationCreateForm
    template_name = 'buildings/photostation_form_update.html'
    #we have two slugs, so we need to override next attribute
    slug_url_kwarg = 'stat_slug'

    def setup(self, request, *args, **kwargs):
        super(PhotoStationUpdateView, self).setup(request, *args, **kwargs)
        #here we get the building by the slug
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )

    def get_object(self, queryset=None):
        #elsewhere we get the parent in setup, but here we also need object
        stat = super(PhotoStationUpdateView, self).get_object(queryset=None)
        if not self.build == stat.build:
            raise Http404(_("Station does not belong to Building"))
        return stat

    def get_initial(self):
        initial = super( PhotoStationUpdateView, self ).get_initial()
        initial['lat'] = self.object.location.coords[1]
        initial['long'] = self.object.location.coords[0]
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #building data
        build = self.build.map_dictionary()
        #plan data
        plans = []
        for plan in self.build.building_plan.all().reverse():
            plan_dict = plan.map_dictionary()
            if plan == self.object.plan:
                plan_dict['visible'] = True
            else:
                plan_dict['visible'] = False
            plans.append(plan_dict)
        #station data
        stat = self.object.map_dictionary()
        context['map_data'] = {
            'build': build,
            'plans': plans,
            'stat': stat,
            'on_map_click': True,
            'no_plan_popup': True,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:station_create',
                kwargs={'slug': self.build.slug}) +
                f'?modified={self.object.title}&model={_("Photo station")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:station_change',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.object.slug }) +
                f'?modified={self.object.title}&model={_("Photo station")}')
        else:
            return (reverse('buildings:station_detail',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.object.slug}) +
                f'?modified={self.object.title}&model={_("Photo station")}')

class PhotoStationDeleteView(VisitorPermReqMix, VisitorPassTestMix, FormView):
    #model = PhotoStation
    permission_required = 'buildings.delete_photostation'
    form_class = BuildingDeleteForm
    template_name = 'buildings/photostation_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(PhotoStationDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.stat = get_object_or_404( PhotoStation,
            slug = self.kwargs['stat_slug'] )
        if not self.build == self.stat.build:
            raise Http404(_("Station does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.stat.title
        return context

    def form_valid(self, form):
        if not 'cancel' in self.request.POST:
            self.stat.delete()
        return super(PhotoStationDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST:
            return reverse( 'buildings:station_detail',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.stat.slug})
        return ( self.build.get_full_path() +
            f'?deleted={self.stat.title}&model={_("Photo station")}')

class PhotoStation3dView( VisitorPermReqMix, VisitorPassTestMix, TemplateView ):
    permission_required = 'buildings.view_photostation'
    template_name = 'buildings/photostation_3d.html'

    def setup(self, request, *args, **kwargs):
        super(PhotoStation3dView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.stat = get_object_or_404( PhotoStation,
            slug = self.kwargs['stat_slug'] )
        if not self.build == self.stat.build:
            raise Http404(_("Station does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stat'] = self.stat
        context['map_data'] = {}
        context['map_data']['stat_id'] = self.stat.id
        #context['map_data']['camera'] = self.stat.camera_position()
        #context['map_data']['geom'] = self.build.get_3d_geometries()
        #context['map_data']['floor'] = self.build.get_floor_elevation()
        return context

class StationImageListCreateView( VisitorPermReqMix, VisitorPassTestMix,
    AlertMixin, CreateView ):
    model = StationImage
    permission_required = ('buildings.view_photostation',)
    form_class = StationImageCreateForm
    template_name = 'buildings/stationimage_list_create.html'

    def setup(self, request, *args, **kwargs):
        super(StationImageListCreateView, self).setup(request, *args, **kwargs)
        #here we get the project by the slug
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.stat = get_object_or_404( PhotoStation,
            slug = self.kwargs['stat_slug'] )
        if not self.stat.build == self.build:
            raise Http404(_("Station does not belong to Building"))

    def get_initial(self):
        initial = super( StationImageListCreateView, self ).get_initial()
        initial['stat'] = self.stat.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stat'] = self.stat
        context = self.add_alerts_to_context(context)
        #we add the following to feed the gallery
        context['main_gal_slug'] = get_random_string(7)
        #gallery images
        if 'reverse' in self.request.GET:
            context['reverse'] = self.request.GET['reverse']
            context['images'] = self.stat.station_image.all().reverse()
        else:
            context['images'] = self.stat.station_image.all()
        return context

    def form_valid(self, form):
        if not self.request.user.has_perm('buildings.add_stationimage'):
            raise Http404(_("User has no permission to add images"))
        return super(StationImageListCreateView, self).form_valid(form)

    def get_success_url(self):
        if 'continue' in self.request.POST:
            return (reverse('buildings:image_change',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.stat.slug,
                'pk': self.object.id }) +
                f'?created={self.object.id}&model={_("Image")}')
        return (reverse('buildings:station_detail',
            kwargs={'build_slug': self.build.slug,
            'stat_slug': self.stat.slug}) +
            f'?created={self.object.id}&model={_("Image")}')

class StationImageUpdateView( VisitorPermReqMix, VisitorPassTestMix, AlertMixin,
    UpdateView ):
    model = StationImage
    permission_required = 'buildings.change_stationimage'
    form_class = StationImageUpdateForm
    template_name = 'buildings/stationimage_form_update.html'

    def setup(self, request, *args, **kwargs):
        super(StationImageUpdateView, self).setup(request, *args, **kwargs)
        #here we get the project by the slug
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.stat = get_object_or_404( PhotoStation,
            slug = self.kwargs['stat_slug'] )
        if not self.stat.build == self.build:
            raise Http404(_("Station does not belong to Building"))

    def get_object(self, queryset=None):
        img = super(StationImageUpdateView, self).get_object(queryset=None)
        if not self.stat == img.stat:
            raise Http404(_("Image does not belong to Photo Station"))
        return img

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_alerts_to_context(context)
        return context

    def get_success_url(self):
        if 'continue' in self.request.POST:
            return (reverse('buildings:image_change',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.stat.slug,
                'pk': self.object.id }) +
                f'?modified={self.object.id}&model={_("Image")}')
        return (reverse('buildings:station_detail',
            kwargs={'build_slug': self.build.slug,
            'stat_slug': self.stat.slug}) +
            f'?modified={self.object.id}&model={_("Image")}')

class StationImageDeleteView(VisitorPermReqMix, VisitorPassTestMix, FormView):
    permission_required = 'buildings.delete_stationimage'
    form_class = BuildingDeleteForm
    template_name = 'buildings/stationimage_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(StationImageDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.stat = get_object_or_404( PhotoStation,
            slug = self.kwargs['stat_slug'] )
        self.img = get_object_or_404( StationImage, id = self.kwargs['pk'])
        if not self.build == self.stat.build:
            raise Http404(_("Station does not belong to Building"))
        if not self.stat == self.img.stat:
            raise Http404(_("Image does not belong to Photo Station"))
        self.title = self.img.id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def form_valid(self, form):
        if not 'cancel' in self.request.POST:
            self.img.delete()
        return super(StationImageDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST:
            return reverse('buildings:station_detail',
                kwargs={'build_slug': self.build.slug,
                'stat_slug': self.stat.slug})
        return (reverse('buildings:station_detail',
            kwargs={'build_slug': self.build.slug,
            'stat_slug': self.stat.slug}) +
            f'?deleted={self.title}&model={_("Image")}')

class StationImageDayArchiveView( VisitorPermReqMix, VisitorPassTestMix,
    DayArchiveView ):
    model = StationImage
    permission_required = 'buildings.view_stationimage'
    date_field = 'date'
    allow_future = True
    context_object_name = 'images'
    year_format = '%Y'
    month_format = '%m'
    day_format = '%d'
    allow_empty = True

    def setup(self, request, *args, **kwargs):
        super(StationImageDayArchiveView, self).setup(request, *args, **kwargs)
        #here we get the project by the slug
        self.build = get_object_or_404( Building, slug = self.kwargs['slug'] )

    def get_queryset(self):
        qs = super(StationImageDayArchiveView, self).get_queryset()
        #here we get the station ids by project related name
        stations = self.build.building_station.values_list('id', flat = True)
        return qs.filter( stat__in = stations ).reverse()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #we add the following to feed the gallery
        context['main_gal_slug'] = get_random_string(7)
        context['build'] = self.build
        return context

class StationImageDayArchiveListView( VisitorPermReqMix, VisitorPassTestMix,
    ListView ):
    model = StationImage
    permission_required = 'buildings.view_stationimage'
    template_name = 'buildings/stationimage_archive_day_list.html'

    def setup(self, request, *args, **kwargs):
        super(StationImageDayArchiveListView, self).setup(request, *args,
            **kwargs)
        #here we get the project by the slug
        self.build = get_object_or_404( Building, slug = self.kwargs['slug'] )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['build'] = self.build
        #add station list
        stat_list = PhotoStation.objects.filter(build_id=self.build.id)
        stat_list = stat_list.values_list('id', flat=True)
        #add dates for images by date
        context['dates'] = StationImage.objects.filter(stat_id__in=stat_list)
        context['dates'] = context['dates'].dates('date', 'day').reverse()
        return context
