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

from bimblog.models import (Building, BuildingPlan, PhotoStation, StationImage,
    DisciplineNode)
from bimblog.forms import ( BuildingCreateForm, BuildingUpdateForm,
    BuildingDeleteForm, BuildingPlanCreateForm,
    DisciplineNodeCreateForm, DisciplineNodeUpdateForm)

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
        path = reverse('bimblog:station_detail',
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
        elif 'disc_created' in self.request.GET:
            context['disc_created'] = self.request.GET['disc_created']
        elif 'disc_modified' in self.request.GET:
            context['disc_modified'] = self.request.GET['disc_modified']
        elif 'disc_deleted' in self.request.GET:
            context['disc_deleted'] = self.request.GET['disc_deleted']
        return context

class BuildingListCreateView( PermissionRequiredMixin, AlertMixin, MapMixin,
    CreateView ):
    model = Building
    permission_required = 'bimblog.view_building'
    form_class = BuildingCreateForm
    template_name = 'bimblog/building_list_create.html'

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
            builds.append( self.prepare_build_data(build) )
        context['map_data'] = {
            'builds': builds,
            'city_lat': settings.CITY_LAT,
            'city_long': settings.CITY_LONG,
            'city_zoom': settings.CITY_ZOOM,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def form_valid(self, form):
        if not self.request.user.has_perm('bimblog.add_building'):
            raise Http404(_("User has no permission to add buildings"))
        return super(BuildingListCreateView, self).form_valid(form)

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('bimblog:building_list') +
                f'?created={self.object.title}')
        else:
            return (reverse('bimblog:building_detail',
                kwargs={'slug': self.object.slug }) +
                f'?created={self.object.title}')

class BuildingDetailView(PermissionRequiredMixin, AlertMixin, MapMixin,
    DetailView):
    model = Building
    permission_required = 'bimblog.view_building'
    context_object_name = 'build'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #add plans and stations
        context['plans'] = context['build'].building_plan.all()
        context['stations'] = context['build'].building_station.all()
        #add station list
        stat_list = context['stations'].values_list('id', flat=True)
        #add dates for images by date
        context['dates'] = StationImage.objects.filter(stat_id__in=stat_list).dates('date', 'day')
        #add alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #building data
        build = self.prepare_build_data( context['build'] )
        #plan data
        disc_list = context['build'].disciplinesn.all().values_list('id',
            flat=True)
        disc_plans = context['plans'].filter(Q(discn=None)|
            Q(discn_id__in=disc_list))
        plans = []
        for plan in disc_plans.reverse():
            plans.append(self.prepare_plan_data(plan))
        #station data
        plan_list = disc_plans.values_list('id', flat=True)
        disc_stat = context['stations'].filter(Q(plan=None)|
            Q(plan_id__in=plan_list))
        stations = []
        for stat in disc_stat:
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
    permission_required = 'bimblog.change_building'
    form_class = BuildingUpdateForm
    template_name = 'bimblog/building_form_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #we add the following to feed the map
        #building data
        build = self.prepare_build_data( self.object )
        context['map_data'] = {
            'build': build,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('bimblog:building_list') +
                f'?modified={self.object.title}')
        else:
            return (reverse('bimblog:building_detail',
                kwargs={'slug': self.object.slug }) +
                f'?modified={self.object.title}')

class BuildingDeleteView(PermissionRequiredMixin, FormView):
    #model = Building
    permission_required = 'bimblog.delete_building'
    form_class = BuildingDeleteForm
    template_name = 'bimblog/building_form_delete.html'

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
            return reverse('bimblog:building_detail',
                kwargs={'slug': self.build.slug })
        return reverse('bimblog:building_list') + f'?deleted={self.build.title}'

class BuildingPlanCreateView( PermissionRequiredMixin, AlertMixin, CreateView ):
    model = BuildingPlan
    permission_required = 'bimblog.add_buildingplan'
    form_class = BuildingPlanCreateForm

    def setup(self, request, *args, **kwargs):
        super(BuildingPlanCreateView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building, slug = self.kwargs['slug'] )

    def get_initial(self):
        initial = super( BuildingPlanCreateView, self ).get_initial()
        initial['build'] = self.build.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_alerts_to_context(context)
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('bimblog:buildingplan_create',
                kwargs={'slug': self.build.slug}) +
                f'?plan_created={self.object.title}')
        else:
            return (reverse('bimblog:building_detail',
                kwargs={'slug': self.build.slug}) +
                f'?plan_created={self.object.title}')

class BuildingPlanUpdateView( PermissionRequiredMixin, UpdateView ):
    model = BuildingPlan
    permission_required = 'bimblog.change_buildingplan'
    form_class = BuildingPlanCreateForm
    template_name = 'bimblog/buildingplan_form_update.html'
    #we have two slugs, so we need to override next attribute
    slug_url_kwarg = 'plan_slug'

    def get_object(self, queryset=None):
        #elsewhere we get the parent in setup, but here we also need object
        plan = super(BuildingPlanUpdateView, self).get_object(queryset=None)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        if not self.build == plan.build:
            raise Http404(_("Plan does not belong to Building"))
        return plan

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('bimblog:buildingplan_create',
                kwargs={'slug': self.build.slug}) +
                f'?plan_modified={self.object.title}')
        else:
            return (reverse('bimblog:building_detail',
                kwargs={'slug': self.build.slug}) +
                f'?plan_modified={self.object.title}')

class BuildingPlanDeleteView(PermissionRequiredMixin, FormView):
    #model = BuildingPlan
    permission_required = 'bimblog.delete_buildingplan'
    form_class = BuildingDeleteForm
    template_name = 'bimblog/buildingplan_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(BuildingPlanDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.plan = get_object_or_404( BuildingPlan,
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
        return super(BuildingPlanDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST:
            return reverse('bimblog:building_detail',
                kwargs={'slug': self.build.slug})
        return (reverse('bimblog:building_detail',
            kwargs={'slug': self.build.slug}) +
            f'?plan_deleted={self.plan.title}')

class DisciplineListCreateView( PermissionRequiredMixin, AlertMixin,
    CreateView ):
    model = DisciplineNode
    permission_required = 'bimblog.view_disciplinenode'
    form_class = DisciplineNodeCreateForm
    template_name = 'bimblog/discipline_list_create.html'

    def setup(self, request, *args, **kwargs):
        super(DisciplineListCreateView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['build'] = self.build
        #list all disciplines as tree
        context['annotated_lists'] = []
        root_pages = DisciplineNode.get_root_nodes()
        for root_page in root_pages:
            context['annotated_lists'].append(DisciplineNode.get_annotated_list(parent=root_page))
        #discipline alerts
        context = self.add_alerts_to_context(context)
        return context

    def form_valid(self, form):
        if not self.request.user.has_perm('bimblog.add_disciplinenode'):
            raise Http404(_("User has no permission to add disciplines"))
        #can't use save method because dealing with MP_Node
        if form.instance.parent:
            self.object = form.instance.parent.add_child(
                title=form.instance.title,
                intro=form.instance.intro)
        else:
            self.object = DisciplineNode.add_root(
                title=form.instance.title,
                intro=form.instance.intro)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('bimblog:discipline_list_create',
                kwargs={'slug': self.build.slug}) +
                f'?disc_created={self.object.title}')
        else:
            return (reverse('bimblog:building_detail',
                kwargs={'slug': self.build.slug}) +
                f'?disc_created={self.object.title}')

class DisciplineUpdateView( PermissionRequiredMixin, UpdateView ):
    model = DisciplineNode
    permission_required = 'bimblog.change_disciplinenode'
    form_class = DisciplineNodeUpdateForm
    template_name = 'bimblog/discipline_form_update.html'

    def setup(self, request, *args, **kwargs):
        super(DisciplineUpdateView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )

    def get_initial(self):
        initial = super( DisciplineUpdateView, self ).get_initial()
        initial['parent'] = self.object.get_parent()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['build'] = self.build
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('bimblog:discipline_list_create',
                kwargs={'slug': self.build.slug}) +
                f'?disc_modified={self.object.title}')
        else:
            return (reverse('bimblog:building_detail',
                kwargs={'slug': self.build.slug}) +
                f'?disc_modified={self.object.title}')

class DisciplineDeleteView(PermissionRequiredMixin, FormView):
    permission_required = 'bimblog.delete_disciplinenode'
    form_class = BuildingDeleteForm
    template_name = 'bimblog/discipline_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(DisciplineDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )
        self.disc = get_object_or_404( DisciplineNode,
            id = self.kwargs['pk'] )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.disc.title
        return context

    def form_valid(self, form):
        if not 'cancel' in self.request.POST:
            self.disc.delete()
        return super(DisciplineDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST:
            return reverse('bimblog:discipline_change',
                kwargs={'slug': self.build.slug, 'pk': self.disc.id})
        return (reverse('bimblog:building_detail',
            kwargs={'slug': self.build.slug}) +
            f'?disc_deleted={self.disc.title}')
