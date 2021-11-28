import json

from django.http import HttpResponseRedirect
from django.db.models import Q
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
    FormView, RedirectView, TemplateView)
from django.views.generic.dates import YearArchiveView, DayArchiveView
from django.utils.crypto import get_random_string
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext as _

from buildings.models import (Building, Plan, PhotoStation, StationImage,
    PlanSet, City, PlanVisibility, Journal)
from buildings.forms import ( BuildingCreateForm, BuildingUpdateForm,
    BuildingDeleteForm, PlanCreateForm,
    PlanSetCreateForm, PlanSetUpdateForm, BuildingAuthenticationForm)

class AlertMixin:
    def add_alerts_to_context(self, context):
        params = [ 'model', 'created', 'modified', 'deleted', ]
        for param in params:
            if param in self.request.GET:
                context[ param ] = self.request.GET[ param ]
        return context

class BuildingRedirectView(LoginView):
    template_name = 'buildings/build_login.html'
    form_class = BuildingAuthenticationForm

    def setup(self, request, *args, **kwargs):
        super(BuildingRedirectView, self).setup(request, *args, **kwargs)
        #control if building exists
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )
        if not self.build.private:
            return HttpResponseRedirect(self.build.get_full_path())
        if not self.build.visitor:
            return HttpResponseRedirect(self.build.get_full_path())
        if request.user.is_authenticated:
            if (request.user.profile.immutable and
                request.user != self.build.visitor):
                raise Http404(_("User is not building visitor"))
            return HttpResponseRedirect(self.build.get_full_path())

    def get_initial(self):
        initial = super( BuildingRedirectView, self ).get_initial()
        initial['username'] = self.build.visitor.username
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['build'] = self.build
        return context

    def get_redirect_url(self, *args, **kwargs):
        return self.build.get_full_path()

class BuildingListView( AlertMixin, TemplateView ):
    #model = Building
    template_name = 'buildings/building_list_new.html'

    #def setup(self, request, *args, **kwargs):
        #super(BuildingListView, self).setup(request, *args, **kwargs)
        #self.city = City.objects.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #list all buildings
        #context['builds'] = Building.objects.all()
        #building alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #not using values() because we have to manipulate entries
        #builds = []
        #for build in context['builds']:
            #builds.append( build.map_dictionary() )
        #if self.city:
            #city_long = self.city.location.coords[0]
            #city_lat = self.city.location.coords[1]
            #city_zoom = self.city.zoom
        #else:
            #city_long = settings.CITY_LONG
            #city_lat = settings.CITY_LAT
            #city_zoom = settings.CITY_ZOOM
        #context['map_data'] = {
            #'builds': builds,
            #'city_lat': city_lat,
            #'city_long': city_long,
            #'city_zoom': city_zoom,
            #'mapbox_token': settings.MAPBOX_TOKEN
            #}
        return context

class BuildingCreateView( PermissionRequiredMixin, AlertMixin, CreateView ):
    model = Building
    permission_required = 'buildings.add_building'
    form_class = BuildingCreateForm
    template_name = 'buildings/building_form.html'

    def setup(self, request, *args, **kwargs):
        super(BuildingCreateView, self).setup(request, *args, **kwargs)
        self.city = City.objects.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #building alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        if self.city:
            city_long = self.city.location.coords[0]
            city_lat = self.city.location.coords[1]
            city_zoom = self.city.zoom
        else:
            city_long = settings.CITY_LONG
            city_lat = settings.CITY_LAT
            city_zoom = settings.CITY_ZOOM
        context['map_data'] = {
            'on_map_click': True,
            'on_map_zoom': True,
            'city_lat': city_lat,
            'city_long': city_long,
            'city_zoom': city_zoom,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def get_initial(self):
        initial = super( BuildingCreateView, self ).get_initial()
        if self.city:
            initial['lat'] = self.city.location.coords[1]
            initial['long'] = self.city.location.coords[0]
        else:
            initial['lat'] = settings.CITY_LAT
            initial['long'] = settings.CITY_LONG
        return initial

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:building_create') +
                f'?created={self.object.title}&model={_("Building")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:building_change',
                kwargs={'slug': self.object.slug }) +
                f'?created={self.object.title}&model={_("Building")}')
        else:
            return ( self.object.get_full_path() +
                f'?created={self.object.title}&model={_("Building")}' )

class BuildingDetailView(AlertMixin, DetailView):
    model = Building
    #permission_required = 'buildings.view_building'
    context_object_name = 'build'
    slug_url_kwarg = 'build_slug'

    def setup(self, request, *args, **kwargs):
        super(BuildingDetailView, self).setup(request, *args, **kwargs)
        if self.get_object().private:
            if not request.user.is_authenticated:
                raise Http404(_("Building is private"))
            if not request.user.has_perm('buildings.view_building'):
                raise Http404(_("User has no permission to view building"))
        self.set = get_object_or_404( PlanSet,
            slug = self.kwargs['set_slug'] )
        if not self.set.build.slug == self.kwargs['build_slug']:
            raise Http404(_("Plan set does not belong to Building"))

    def get(self, request, *args, **kwargs):
        if 'visibility' in request.GET and request.user.has_perm('buildings.change_plan'):
            pv = get_object_or_404( PlanVisibility,
                id=request.GET['visibility'])
            if pv.visibility:
                pv.visibility = False
            else:
                pv.visibility = True
            pv.save()
        return super(BuildingDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #add plansets
        context['annotated_list'] = self.object.get_planset_annotated_list()
        #add plans
        context['planset'] = self.set
        context['plans'], context['plan_visibility'] = (self.set.
            get_self_and_ancestor_plans())
        plan_list = context['plans'].values_list('id', flat=True)
        #add families
        context['fam_annotated_list'] = self.object.get_family_annotated_list()
        #add elements
        context['elements'] = self.object.building_element.filter(Q(plan=None)|
            Q(plan_id__in=plan_list))
        #add stations
        context['stations'] = self.object.building_station.filter(Q(plan=None)|
            Q(plan_id__in=plan_list))
        stat_list = PhotoStation.objects.filter(build_id=self.object.id)
        stat_list = stat_list.values_list('id', flat=True)
        #add dates for images by date
        context['dates'] = StationImage.objects.filter(stat_id__in=stat_list)
        if context['dates'].count() > 5:
            context['dates_link'] = True
        context['dates'] = context['dates'].dates('date', 'day').reverse()[:5]
        #add journals
        context['journals'] = self.object.building_journal.all()
        if context['journals'].count() > 5:
            context['jour_link'] = True
        context['journals'] = context['journals'][:5]
        #add alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #building data
        build = self.object.map_dictionary()
        #plan data
        plans = []
        for plan in context['plans'].reverse():
            plan_temp = plan.map_dictionary()
            visibility = context['plan_visibility'][plan]
            plan_temp['visible'] = visibility[1]
            plans.append(plan_temp)
        #element data
        elements = []
        for elem in context['elements']:
            elements.append(elem.map_dictionary())
        #station data
        stations = []
        for stat in context['stations']:
            stations.append(stat.map_dictionary())
        #are there stations that don't belong to plans?
        no_plan_status = False
        if context['elements'].filter(plan_id=None):
            no_plan_status = True
        if context['stations'].filter(plan_id=None):
            no_plan_status = True
        context['map_data'] = {
            'build': build,
            'plans': plans,
            'elements': elements,
            'stations': stations,
            'no_plan_status': no_plan_status,
            'no_plan_trans': _("No plan"),
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

class BuildingUpdateView(PermissionRequiredMixin, AlertMixin, UpdateView):
    model = Building
    permission_required = 'buildings.change_building'
    form_class = BuildingUpdateForm
    template_name = 'buildings/building_form_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #building alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #building data
        build = self.object.map_dictionary()
        context['map_data'] = {
            'build': build,
            'on_map_click': True,
            'on_map_zoom': True,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def get_initial(self):
        initial = super( BuildingUpdateView, self ).get_initial()
        initial['lat'] = self.object.location.coords[1]
        initial['long'] = self.object.location.coords[0]
        return initial

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:building_list') +
                f'?modified={self.object.title}&model={_("Building")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:building_change',
                kwargs={'slug': self.object.slug }) +
                f'?modified={self.object.title}&model={_("Building")}')
        else:
            return ( self.object.get_full_path() +
                f'?modified={self.object.title}&model={_("Building")}')

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
            return reverse('buildings:building_slug',
                kwargs={'slug': self.build.slug })
        return (reverse('buildings:building_list') +
            f'?deleted={self.build.title}&model={_("Building")}')

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

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:plan_create',
                kwargs={'slug': self.build.slug}) +
                f'?created={self.object.title}&model={_("Plan")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:plan_change',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.object.slug }) +
                f'?created={self.object.title}&model={_("Plan")}')
        else:
            return (reverse('buildings:plan_detail',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.object.slug}) +
                f'?created={self.object.title}&model={_("Plan")}')

class PlanUpdateView( PermissionRequiredMixin, AlertMixin, UpdateView ):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #building alerts
        context = self.add_alerts_to_context(context)
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:plan_create',
                kwargs={'slug': self.build.slug}) +
                f'?modified={self.object.title}&model={_("Plan")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:plan_change',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.object.slug }) +
                f'?modified={self.object.title}&model={_("Plan")}')
        else:
            return (reverse('buildings:plan_detail',
                kwargs={'build_slug': self.build.slug,
                'plan_slug': self.object.slug}) +
                f'?modified={self.object.title}&model={_("Plan")}')

class PlanDetailView(PermissionRequiredMixin, AlertMixin, DetailView):
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
        context['annotated_list'] = self.build.get_planset_annotated_list()
        #add plans
        context['plans'] = self.build.building_plan.all()
        #add elements
        context['elements'] = self.build.building_element.filter(
            plan_id=self.object.id)
        #add stations
        context['stations'] = self.build.building_station.all()
        stat_list = context['stations'].values_list('id', flat=True)
        #add dates for images by date
        context['dates'] = StationImage.objects.filter(stat_id__in=stat_list)
        context['dates'] = context['dates'].dates('date', 'day')
        #add alerts
        context = self.add_alerts_to_context(context)
        #we add the following to feed the map
        #building data
        build = self.build.map_dictionary()
        #plan data
        plans = []
        for plan in context['plans'].reverse():
            plan_dict = plan.map_dictionary()
            if plan == self.object:
                plan_dict['visible'] = True
            else:
                plan_dict['visible'] = False
            plans.append(plan_dict)
        #element data
        elements = []
        for elem in context['elements']:
            elements.append(elem.map_dictionary())
        #are there stations that don't belong to plans?
        no_plan_status = False
        context['map_data'] = {
            'build': build,
            'plans': plans,
            'elements': elements,
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
            return self.build.get_full_path()
        return ( self.build.get_full_path() +
            f'?deleted={self.plan.title}&model={_("Plan")}')

class PlanSetCreateView( PermissionRequiredMixin, AlertMixin, CreateView ):
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
        initial['parent'] = PlanSet.objects.get(slug=self.build.get_base_slug()).id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #planset alerts
        context = self.add_alerts_to_context(context)
        return context

    def form_valid(self, form):
        #can't use save method because dealing with MP_Node
        self.object = form.instance.parent.add_child(
            build=self.build,
            title=form.instance.title,
            intro=form.instance.intro)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:planset_create',
                kwargs={'slug': self.build.slug}) +
                f'?created={self.object.title}&model={_("Plan set")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:planset_change',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.object.slug }) +
                f'?created={self.object.title}&model={_("Plan set")}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.object.slug}) +
                f'?created={self.object.title}&model={_("Plan set")}')

class PlanSetUpdateView( PermissionRequiredMixin, AlertMixin, UpdateView ):
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
        #building alerts
        context = self.add_alerts_to_context(context)
        context['build'] = self.build
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:planset_create',
                kwargs={'slug': self.build.slug}) +
                f'?modified={self.object.title}&model={_("Plan set")}')
        elif 'continue' in self.request.POST:
            return (reverse('buildings:planset_change',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.object.slug }) +
                f'?modified={self.object.title}&model={_("Plan set")}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.object.slug}) +
                f'?modified={self.object.title}&model={_("Plan set")}')

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
        if (not 'cancel' in self.request.POST and
            not self.set.slug.startswith('base_')):
            self.set.delete()
        return super(PlanSetDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST or self.set.slug.startswith('base_'):
            return reverse('buildings:planset_change',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.set.slug})
        return ( self.build.get_full_path() +
            f'?deleted={self.set.title}&model={_("Plan set")}')

class JournalDetailView( DetailView ):
    model = Journal
    context_object_name = 'jour'
    slug_url_kwarg = 'jour_slug'

    def setup(self, request, *args, **kwargs):
        super(JournalDetailView, self).setup(request, *args, **kwargs)
        #here we get the project by the slug
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        if self.build.private:
            if not request.user.is_authenticated:
                raise Http404(_("Building is private"))
            if not request.user.has_perm('buildings.view_journal'):
                raise Http404(_("User has no permission to view the journal"))
        self.jour = get_object_or_404( Journal,
            slug = self.kwargs['jour_slug'] )
        if not self.jour.build == self.build:
            raise Http404(_("Journal does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #we add the following to feed the gallery
        context['main_gal_slug'] = get_random_string(7)
        #get all images belonging to this building with same date as journal
        stations = self.build.building_station.values_list('id', flat = True)
        context['images'] = StationImage.objects.filter(
            date__date = self.object.date, stat__in = stations).reverse()
        context['day'] = self.object.date
        context['prev'] = self.object.get_previous()
        context['next'] = self.object.get_next()
        context['build'] = self.build
        return context

    def get_template_names(self):
        if 'PDF' in self.request.GET:
            return ['buildings/journal_pdf.html', ]
        return ['buildings/journal_detail.html', ]

class JournalListView( ListView ):
    model = Journal
    template_name = 'buildings/journal_list.html'

    def setup(self, request, *args, **kwargs):
        super(JournalListView, self).setup(request, *args, **kwargs)
        #here we get the project by the slug
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )
        if self.build.private:
            if not request.user.is_authenticated:
                raise Http404(_("Building is private"))
            if not request.user.has_perm('buildings.view_journal'):
                raise Http404(_("User has no permission to view journals"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['build'] = self.build
        #add journals
        context['journals'] = self.build.building_journal.all()
        return context
