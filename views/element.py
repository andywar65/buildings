import csv

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import ( CreateView, UpdateView, FormView,)
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
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
                f'?created={self.object.title}&model={_("Element family")}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.build.get_base_slug()}) +
                f'?created={self.object.title}&model={_("Element family")}')

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
                f'?modified={self.object.title}&model={_("Element family")}')
        else:
            return (reverse('buildings:building_detail',
                kwargs={'build_slug': self.build.slug,
                'set_slug': self.build.get_base_slug()}) +
                f'?modified={self.object.title}&model={_("Element family")}')

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
            f'?deleted={self.fam.title}&model={_("Element family")}')

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
                f'?created={self.object.__str__()}&model={_("Element")}')
        else:
            return (self.object.get_building_redirection() +
                f'?created={self.object.__str__()}&model={_("Element")}')

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
                f'?modified={self.object.__str__()}&model={_("Element")}')
        else:
            return (self.object.get_building_redirection() +
                f'?modified={self.object.__str__()}&model={_("Element")}')

class ElementDeleteView(PermissionRequiredMixin, FormView):
    permission_required = 'buildings.delete_element'
    form_class = BuildingDeleteForm
    template_name = 'buildings/element_form_delete.html'

    def setup(self, request, *args, **kwargs):
        super(ElementDeleteView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building,
            slug = self.kwargs['slug'] )
        self.elem = get_object_or_404( Element,
            id = self.kwargs['pk'] )
        self.title = self.elem.__str__()
        if not self.build == self.elem.build:
            raise Http404(_("Element does not belong to Building"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def form_valid(self, form):
        if not 'cancel' in self.request.POST:
            self.elem.delete()
        return super(ElementDeleteView, self).form_valid(form)

    def get_success_url(self):
        if 'cancel' in self.request.POST:
            return reverse('buildings:element_change',
                kwargs={'slug': self.build.slug,
                'pk': self.elem.id})
        return (reverse('buildings:building_detail',
            kwargs={'build_slug': self.build.slug,
            'set_slug': self.build.get_base_slug()}) +
            f'?deleted={self.title}&model={_("Element")}')

def csv_writer(writer, qs):
    writer.writerow([_('Building'), _('Family'), _('Plan'), _('Image'),
        _('Description'), _('Latitude'), _('Longitude'), _('Data sheet')])
    for e in qs:
        image = e.fb_image.url if e.fb_image else _('No image')
        intro = e.intro if e.intro else _('No description')
        row = [e.build, e.family, e.plan, image, intro, e.lat, e.long]
        for key, value in e.sheet.items():
            row.append(key)
            row.append(value)
        writer.writerow(row)
    return writer

@permission_required('buildings.view_building')
def building_element_download(request, slug):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="%(building)s-elements.csv"' %
        { 'building': _('Buildings') }
        )
    build = get_object_or_404( Building, slug = slug )
    qs = Element.objects.filter(build_id=build.id)

    writer = csv.writer(response)
    writer = csv_writer(writer, qs)

    return response
