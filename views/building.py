from django.http import HttpResponseRedirect
from django.db.models import Q
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
    FormView,)
from django.views.generic.dates import YearArchiveView, DayArchiveView
from django.utils.crypto import get_random_string
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext as _

from buildings.models import (Building, Plan, PhotoStation, StationImage,
    PlanSet)
from buildings.forms import ( BuildingCreateForm, BuildingUpdateForm,
    BuildingDeleteForm, PlanCreateForm,
    PlanSetCreateForm, PlanSetUpdateForm)

class MapMixin:

    def prepare_build_data(self, build):
        build.fb_image.version_generate("medium")
        fb_path = (settings.MEDIA_URL +
            build.fb_image.version_path("medium"))
        return {'title': build.title, 'intro': build.intro,
            'path': build.get_full_path(), 'lat': build.lat,
            'long': build.long, 'zoom': build.zoom, 'fb_path': fb_path}

    def prepare_plan_data(self, plan):
        return {'id': plan.id, 'geometry': plan.geometry,
            'title': plan.title, 'visible': plan.visible}

    def prepare_stat_data(self, stat):
        if stat.station_image.first():
            stat.station_image.first().fb_image.version_generate("medium")
            fb_path = (settings.MEDIA_URL +
                stat.station_image.first().fb_image.version_path("medium"))
        else:
            fb_path = ''
        path = reverse('buildings:station_detail',
            kwargs={'build_slug': stat.build.slug,
            'stat_slug': stat.slug})
        return {'id': stat.id, 'title': stat.title, 'path': path,
            'fb_path': fb_path, 'lat': stat.lat, 'long': stat.long,
            'intro': stat.intro, 'plan_id': stat.plan_id}

class AlertMixin:
    def add_alerts_to_context(self, context):
        if 'created' in self.request.GET:
            context['created'] = self.request.GET['created']
        elif 'modified' in self.request.GET:
            context['modified'] = self.request.GET['modified']
        elif 'deleted' in self.request.GET:
            context['deleted'] = self.request.GET['deleted']
        elif 'plan_created' in self.request.GET:
            context['plan_created'] = self.request.GET['plan_created']
        elif 'plan_modified' in self.request.GET:
            context['plan_modified'] = self.request.GET['plan_modified']
        elif 'plan_deleted' in self.request.GET:
            context['plan_deleted'] = self.request.GET['plan_deleted']
        elif 'stat_created' in self.request.GET:
            context['stat_created'] = self.request.GET['stat_created']
        elif 'stat_modified' in self.request.GET:
            context['stat_modified'] = self.request.GET['stat_modified']
        elif 'stat_deleted' in self.request.GET:
            context['stat_deleted'] = self.request.GET['stat_deleted']
        elif 'img_created' in self.request.GET:
            context['img_created'] = self.request.GET['img_created']
        elif 'img_modified' in self.request.GET:
            context['img_modified'] = self.request.GET['img_modified']
        elif 'img_deleted' in self.request.GET:
            context['img_deleted'] = self.request.GET['img_deleted']
        elif 'set_created' in self.request.GET:
            context['set_created'] = self.request.GET['set_created']
        elif 'set_modified' in self.request.GET:
            context['set_modified'] = self.request.GET['set_modified']
        elif 'set_deleted' in self.request.GET:
            context['set_deleted'] = self.request.GET['set_deleted']
        return context

class BuildingListCreateView( PermissionRequiredMixin, AlertMixin, CreateView ):
    model = Building
    permission_required = 'buildings.view_building'
    form_class = BuildingCreateForm
    template_name = 'buildings/building_list_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #list all buildings
        context['builds'] = Building.objects.all()
        #building alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #not using values() because we have to manipulate entries
        builds = []
        for build in context['builds']:
            builds.append( build.map_dictionary() )
        context['map_data'] = {
            'builds': builds,
            'on_map_click': True,
            'city_lat': settings.CITY_LAT,
            'city_long': settings.CITY_LONG,
            'city_zoom': settings.CITY_ZOOM,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def form_valid(self, form):
        if not self.request.user.has_perm('buildings.add_building'):
            raise Http404(_("User has no permission to add buildings"))
        return super(BuildingListCreateView, self).form_valid(form)

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:building_list') +
                f'?created={self.object.title}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.object.slug,
                'set_slug': 'base_'+str(self.object.id) }) +
                f'?created={self.object.title}')

class BuildingDetailView(PermissionRequiredMixin, AlertMixin, MapMixin,
    DetailView):
    model = Building
    permission_required = 'buildings.view_building'
    context_object_name = 'build'
    slug_url_kwarg = 'build_slug'

    def setup(self, request, *args, **kwargs):
        super(BuildingDetailView, self).setup(request, *args, **kwargs)
        self.set = get_object_or_404( PlanSet,
            slug = self.kwargs['set_slug'],
            build__slug=self.kwargs['build_slug'] )
        if not self.set.build.slug == self.kwargs['build_slug']:
            raise Http404(_("Plan set does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #add plansets
        plansets = self.object.building_planset.all()
        context['annotated_lists'] = []
        for planset in plansets:
            if planset.is_root():
                context['annotated_lists'].append(PlanSet.get_annotated_list(parent=planset))
        #add plans
        context['planset'] = self.set
        context['plans'] = self.set.plans.all()
        for ancestor in context['planset'].get_ancestors():
            ancestor_plans = ancestor.plans.all()
            context['plans'] = context['plans'] | ancestor_plans
        context['plans'] = context['plans'].distinct().order_by('elev')
        plan_list = context['plans'].values_list('id', flat=True)
        #add stations
        context['stations'] = self.object.building_station.filter(Q(plan=None)|
            Q(plan_id__in=plan_list))
        stat_list = PhotoStation.objects.filter(build_id=self.object.id).values_list('id', flat=True)
        #add dates for images by date
        context['dates'] = StationImage.objects.filter(stat_id__in=stat_list).dates('date', 'day')
        #add alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #building data
        build = self.prepare_build_data( self.object )
        #plan data
        plans = []
        for plan in context['plans'].reverse():
            plans.append(self.prepare_plan_data(plan))
        #station data
        stations = []
        for stat in context['stations']:
            stations.append(self.prepare_stat_data(stat))
        #are there stations that don't belong to plans?
        no_plan_status = False
        if context['stations'].filter(plan_id=None):
            no_plan_status = True
        context['map_data'] = {
            'build': build,
            'plans': plans,
            'stations': stations,
            'no_plan_status': no_plan_status,
            'no_plan_trans': _("No plan"),
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

class BuildingUpdateView(PermissionRequiredMixin, MapMixin, UpdateView):
    model = Building
    permission_required = 'buildings.change_building'
    form_class = BuildingUpdateForm
    template_name = 'buildings/building_form_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #we add the following to feed the map
        #building data
        build = self.prepare_build_data( self.object )
        context['map_data'] = {
            'build': build,
            'on_map_click': True,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:building_list') +
                f'?modified={self.object.title}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.object.slug,
                'set_slug': 'base_'+str(self.object.id) }) +
                f'?modified={self.object.title}')

class BuildingDeleteView(PermissionRequiredMixin, FormView):
    #model = Building
    permission_required = 'buildings.delete_building'
    form_class = BuildingDeleteForm
    template_name = 'buildings/building_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(BuildingDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building, slug = self.kwargs['slug'] )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.build.title
        return context

    def form_valid(self, form):
        if not 'cancel' in self.request.POST:
            self.build.delete()
        return super(BuildingDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST:
            return reverse('buildings:building_detail',
                kwargs={'slug': self.build.slug })
        return reverse('buildings:building_list') + f'?deleted={self.build.title}'

class PlanCreateView( PermissionRequiredMixin, AlertMixin, CreateView ):
    model = Plan
    permission_required = 'buildings.add_plan'
    form_class = PlanCreateForm

    def setup(self, request, *args, **kwargs):
        super(PlanCreateView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building, slug = self.kwargs['slug'] )

    def get_initial(self):
        initial = super( PlanCreateView, self ).get_initial()
        initial['build'] = self.build.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_alerts_to_context(context)
        return context

    def form_valid(self, form):
        return super(PlanCreateView, self).form_valid(form)
        object = self.object

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:plan_create',
                kwargs={'slug': self.build.slug}) +
                f'?plan_created={self.object.title}')
        else:
            return (reverse('buildings:plan_detail',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.object.slug}) +
                f'?plan_created={self.object.title}')

class PlanUpdateView( PermissionRequiredMixin, UpdateView ):
    model = Plan
    permission_required = 'buildings.change_plan'
    form_class = PlanCreateForm
    template_name = 'buildings/plan_form_update.html'
    #we have two slugs, so we need to override next attribute
    slug_url_kwarg = 'plan_slug'

    def get_object(self, queryset=None):
        #elsewhere we get the parent in setup, but here we also need object
        plan = super(PlanUpdateView, self).get_object(queryset=None)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        if not self.build == plan.build:
            raise Http404(_("Plan does not belong to Building"))
        return plan

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:plan_create',
                kwargs={'slug': self.build.slug}) +
                f'?plan_modified={self.object.title}')
        else:
            return (reverse('buildings:plan_detail',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.object.slug}) +
                f'?plan_modified={self.object.title}')

class PlanDetailView(PermissionRequiredMixin, AlertMixin, MapMixin,
    DetailView):
    model = Plan
    permission_required = 'buildings.view_plan'
    context_object_name = 'plan'
    slug_url_kwarg = 'plan_slug'

    def get_object(self, queryset=None):
        #elsewhere we get the parent in setup, but here we also need object
        plan = super(PlanDetailView, self).get_object(queryset=None)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        if not self.build == plan.build:
            raise Http404(_("Plan does not belong to Building"))
        return plan

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #add building
        context['build'] = self.build
        #add plansets
        plansets = self.build.building_planset.all()
        context['annotated_lists'] = []
        for planset in plansets:
            if planset.is_root():
                context['annotated_lists'].append(PlanSet.get_annotated_list(parent=planset))
        #add plans
        context['plans'] = self.build.building_plan.all()
        #add stations
        context['stations'] = self.build.building_station.all()
        stat_list = context['stations'].values_list('id', flat=True)
        #add dates for images by date
        context['dates'] = StationImage.objects.filter(stat_id__in=stat_list).dates('date', 'day')
        #add alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #building data
        build = self.prepare_build_data( self.build )
        #plan data
        plans = []
        for plan in context['plans'].reverse():
            plan_dict = self.prepare_plan_data(plan)
            if plan == self.object:
                plan_dict['visible'] = True
            else:
                plan_dict['visible'] = False
            plans.append(plan_dict)
        #are there stations that don't belong to plans?
        no_plan_status = False
        context['map_data'] = {
            'build': build,
            'plans': plans,
            'stations': False,
            'no_plan_status': no_plan_status,
            'no_plan_trans': _("No plan"),
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

class PlanDeleteView(PermissionRequiredMixin, FormView):
    #model = Plan
    permission_required = 'buildings.delete_plan'
    form_class = BuildingDeleteForm
    template_name = 'buildings/plan_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(PlanDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.plan = get_object_or_404( Plan,
            slug = self.kwargs['plan_slug'] )
        if not self.build == self.plan.build:
            raise Http404(_("Plan does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.plan.title
        return context

    def form_valid(self, form):
        if not 'cancel' in self.request.POST:
            self.plan.delete()
        return super(PlanDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST:
            return reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': 'base_'+str(self.build.id)})
        return (reverse('buildings:building_detail',
            kwargs={'build_slug': self.build.slug,
            'set_slug': 'base_'+str(self.build.id)}) +
            f'?plan_deleted={self.plan.title}')

class PlanSetCreateView( PermissionRequiredMixin, AlertMixin,
    CreateView ):
    model = PlanSet
    permission_required = 'buildings.add_planset'
    form_class = PlanSetCreateForm
    template_name = 'buildings/planset_form.html'

    def setup(self, request, *args, **kwargs):
        super(PlanSetCreateView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )

    def get_initial(self):
        initial = super( PlanSetCreateView, self ).get_initial()
        initial['build'] = self.build.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #planset alerts
        context = self.add_alerts_to_context(context)
        return context

    def form_valid(self, form):
        #can't use save method because dealing with MP_Node
        if form.instance.parent:
            self.object = form.instance.parent.add_child(
                build=self.build,
                title=form.instance.title,
                intro=form.instance.intro)
        else:
            self.object = PlanSet.add_root(
                build=self.build,
                title=form.instance.title,
                intro=form.instance.intro)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:planset_create',
                kwargs={'slug': self.build.slug}) +
                f'?set_created={self.object.title}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.object.slug}) +
                f'?set_created={self.object.title}')

class PlanSetUpdateView( PermissionRequiredMixin, UpdateView ):
    model = PlanSet
    permission_required = 'buildings.change_planset'
    form_class = PlanSetUpdateForm
    template_name = 'buildings/planset_form_update.html'
    slug_url_kwarg = 'set_slug'

    def get_object(self, queryset=None):
        #elsewhere we get the parent in setup, but here we also need object
        set = super(PlanSetUpdateView, self).get_object(queryset=None)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        if not self.build == set.build:
            raise Http404(_("Plan set does not belong to Building"))
        return set

    def get_initial(self):
        initial = super( PlanSetUpdateView, self ).get_initial()
        initial['parent'] = self.object.get_parent()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['build'] = self.build
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:planset_create',
                kwargs={'slug': self.build.slug}) +
                f'?set_modified={self.object.title}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.object.slug}) +
                f'?set_modified={self.object.title}')

class PlanSetDeleteView(PermissionRequiredMixin, FormView):
    permission_required = 'buildings.delete_planset'
    form_class = BuildingDeleteForm
    template_name = 'buildings/planset_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(PlanSetDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.set = get_object_or_404( PlanSet,
            slug = self.kwargs['set_slug'] )
        if not self.build == self.set.build:
            raise Http404(_("Plan set does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.set.title
        return context

    def form_valid(self, form):
        if not 'cancel' in self.request.POST and not self.set.slug.startswith('base_'):
            self.set.delete()
        return super(PlanSetDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST or self.set.slug.startswith('base_'):
            return reverse('buildings:planset_change',
                kwargs={'build_slug': self.build.slug, 'set_slug': self.set.slug})
        return (reverse('buildings:building_detail',
            kwargs={'build_slug': self.build.slug,
            'set_slug': 'base_'+str(self.build.id)}) +
            f'?set_deleted={self.set.title}')
