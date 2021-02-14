from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import ( CreateView, UpdateView, FormView,)
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext as _

from buildings.models import (Building, Family, Element)
from buildings.forms import ( FamilyCreateForm, FamilyUpdateForm,
    BuildingDeleteForm, ElementCreateForm)
from buildings.views.building import AlertMixin

class FamilyListCreateView( PermissionRequiredMixin, AlertMixin, CreateView ):
    model = Family
    permission_required = 'buildings.add_family'
    form_class = FamilyCreateForm
    template_name = 'buildings/family_list_create.html'

    def setup(self, request, *args, **kwargs):
        super(FamilyListCreateView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )

    def get_initial(self):
        initial = super( FamilyListCreateView, self ).get_initial()
        initial['build'] = self.build.id
        initial['sheet'] = { 'Feature 1': 'Value 1', 'Feature 2': 'Value 2' }
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #planset alerts
        context['annotated_list'] = self.build.get_family_annotated_list()
        context = self.add_alerts_to_context(context)
        return context

    def form_valid(self, form):
        #can't use save method because dealing with MP_Node
        self.object = form.instance.parent.add_child(
            build=self.build,
            title=form.instance.title,
            intro=form.instance.intro,
            sheet=form.instance.sheet)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:family_list_create',
                kwargs={'slug': self.build.slug}) +
                f'?fam_created={self.object.title}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.build.get_base_slug()}) +
                f'?fam_created={self.object.title}')

class FamilyUpdateView( PermissionRequiredMixin, UpdateView ):
    model = Family
    permission_required = 'buildings.change_family'
    form_class = FamilyUpdateForm
    template_name = 'buildings/family_form_update.html'
    slug_url_kwarg = 'fam_slug'

    def get_object(self, queryset=None):
        #elsewhere we get the parent in setup, but here we also need object
        fam = super(FamilyUpdateView, self).get_object(queryset=None)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        if not self.build == fam.build:
            raise Http404(_("Element family does not belong to Building"))
        return fam

    def get_initial(self):
        initial = super( FamilyUpdateView, self ).get_initial()
        initial['parent'] = self.object.get_parent()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['build'] = self.build
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:family_create',
                kwargs={'slug': self.build.slug}) +
                f'?fam_modified={self.object.title}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.build.get_base_slug()}) +
                f'?fam_modified={self.object.title}')

class FamilyDeleteView(PermissionRequiredMixin, FormView):
    permission_required = 'buildings.delete_family'
    form_class = BuildingDeleteForm
    template_name = 'buildings/family_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(FamilyDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['build_slug'] )
        self.fam = get_object_or_404( Family,
            slug = self.kwargs['fam_slug'] )
        if not self.build == self.fam.build:
            raise Http404(_("Element family does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.fam.title
        return context

    def form_valid(self, form):
        if (not 'cancel' in self.request.POST and
            not self.fam.slug.startswith('base_')):
            self.fam.delete()
        return super(FamilyDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST or self.fam.slug.startswith('base_'):
            return reverse('buildings:family_change',
                kwargs={'build_slug': self.build.slug,
                'fam_slug': self.fam.slug})
        return (reverse('buildings:building_detail',
            kwargs={'build_slug': self.build.slug,
            'set_slug': self.build.get_base_slug()}) +
            f'?fam_deleted={self.fam.title}')

class ElementCreateView( PermissionRequiredMixin, AlertMixin, CreateView ):
    model = Element
    permission_required = 'buildings.add_element'
    form_class = ElementCreateForm

    def setup(self, request, *args, **kwargs):
        super(ElementCreateView, self).setup(request, *args, **kwargs)
        #here we get the building by the slug
        self.build = get_object_or_404( Building, slug = self.kwargs['slug'] )

    def get_initial(self):
        initial = super( ElementCreateView, self ).get_initial()
        initial['build'] = self.build.id
        initial['sheet'] = { 'Feature 1': 'Value 1', 'Feature 2': 'Value 2' }
        initial['lat'] = self.build.lat
        initial['long'] = self.build.long
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
            return (reverse('buildings:element_create',
                kwargs={'slug': self.build.slug}) +
                f'?elem_created={self.object.__str__()}')
        else:
            return (self.object.get_building_redirection() +
                f'?elem_created={self.object.__str__()}')

class ElementUpdateView( PermissionRequiredMixin, UpdateView ):
    model = Element
    permission_required = 'buildings.change_element'
    form_class = ElementCreateForm
    template_name = 'buildings/element_form_update.html'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        #elsewhere we get the parent in setup, but here we also need object
        elem = super(ElementUpdateView, self).get_object(queryset=None)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )
        if not self.build == elem.build:
            raise Http404(_("Element does not belong to Building"))
        return elem

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.__str__()
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
        #element data
        element = self.object.map_dictionary()
        context['map_data'] = {
            'build': build,
            'plans': plans,
            'elem': element,
            'on_map_click': True,
            'no_plan_popup': True,
            'mapbox_token': settings.MAPBOX_TOKEN
            }
        return context

    def get_success_url(self):
        if 'add_another' in self.request.POST:
            return (reverse('buildings:element_create',
                kwargs={'slug': self.build.slug}) +
                f'?elem_modified={self.object.__str__()}')
        else:
            return (self.object.get_building_redirection() +
                f'?elem_modified={self.object.__str__()}')
