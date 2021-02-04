from django import forms
from django.forms import ModelForm, ModelChoiceField, ModelMultipleChoiceField
from django.utils.translation import gettext as _

from .models import (Building, Plan, PhotoStation, StationImage,
    PlanSet)

class NodeMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        prefix = ''
        for i in range( obj.depth -1 ):
            prefix = prefix + '-'
        return prefix + obj.title

class BuildingCreateForm(ModelForm):
    image = forms.ImageField(label=_('Image'), required=True)
    plansets = NodeMultipleChoiceField(label=_('Disciplines'),
        queryset=PlanSet.objects.all(), required=False,
        help_text=_("Show only plans belonging to chosen disciplines"))

    class Meta:
        model = Building
        fields = ( 'image', 'title', 'intro', 'date', 'address', 'lat', 'long',
            'zoom', 'plansets')

class BuildingUpdateForm(ModelForm):
    plansets = NodeMultipleChoiceField(label=_('Disciplines'),
        queryset=PlanSet.objects.all(), required=False,
        help_text=_("Show only plans belonging to chosen disciplines"))

    class Meta:
        model = Building
        fields = ( 'image', 'title', 'intro', 'date', 'address', 'lat', 'long',
            'zoom', 'plansets')

class BuildingDeleteForm(forms.Form):
    delete = forms.BooleanField( label=_("Delete the building"),
        required = False,
        help_text = _("""Caution, can't undo this."""))

class PlanCreateForm(ModelForm):
    build = forms.ModelChoiceField( label=_('Building'),
        queryset=Building.objects.all(), disabled = True )

    class Meta:
        model = Plan
        fields = '__all__'

class PhotoStationCreateForm(ModelForm):
    build = forms.ModelChoiceField( label=_('Building'),
        queryset=Building.objects.all(), disabled = True )

    def __init__(self, **kwargs):
        super(PhotoStationCreateForm, self).__init__(**kwargs)
        #filter plan queryset
        self.fields['plan'].queryset = Plan.objects.filter(build_id=self.initial['build'])

    class Meta:
        model = PhotoStation
        fields = '__all__'

class StationImageCreateForm(ModelForm):
    stat = forms.ModelChoiceField( label=_('Photo station'),
        queryset=PhotoStation.objects.all(), disabled = True )
    image = forms.ImageField(label=_('Image'), required=True)

    class Meta:
        model = StationImage
        fields = ( 'image', 'stat', 'date', 'caption')

class StationImageUpdateForm(ModelForm):
    stat = forms.ModelChoiceField( label=_('Photo station'),
        queryset=PhotoStation.objects.all(), disabled = True )

    class Meta:
        model = StationImage
        fields = ( 'image', 'stat', 'date', 'caption')

class NodeChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        prefix = ''
        for i in range( obj.depth -1 ):
            prefix = prefix + '-'
        return prefix + obj.title

class PlanSetCreateForm(ModelForm):
    parent = NodeChoiceField( label=_('Parent discipline'),
        queryset=PlanSet.objects.all(), required=False,
        help_text = _('Choose carefully: can be changed only by staff in admin'))
    class Meta:
        model = PlanSet
        fields = ('parent', 'title', 'intro')

class PlanSetUpdateForm(ModelForm):
    parent = NodeChoiceField( label=_('Parent discipline'),
        queryset=PlanSet.objects.all(), disabled = True,
        help_text = _('Can be changed only by staff in admin'))
    class Meta:
        model = PlanSet
        fields = ('parent', 'title', 'intro')
