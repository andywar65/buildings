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

    class Meta:
        model = Building
        fields = ( 'image', 'title', 'intro', 'date', 'address', 'lat', 'long',
            'zoom', )

class BuildingUpdateForm(ModelForm):

    class Meta:
        model = Building
        fields = ( 'image', 'title', 'intro', 'date', 'address', 'lat', 'long',
            'zoom', )

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

class PlanSetCreateForm(ModelForm):
    build = forms.ModelChoiceField( label=_('Building'),
        queryset=Building.objects.all(), disabled = True )

    def __init__(self, **kwargs):
        super(PlanSetCreateForm, self).__init__(**kwargs)
        #filter plan queryset
        self.fields['plans'].queryset = Plan.objects.filter(build_id=self.initial['build'])
        self.fields['parent'].queryset = PlanSet.objects.filter(build_id=self.initial['build'])

    class Meta:
        model = PlanSet
        fields = ('build', 'parent', 'title', 'intro', 'plans')

class PlanSetUpdateForm(ModelForm):
    build = forms.ModelChoiceField( label=_('Building'),
        queryset=Building.objects.all(), disabled = True )
    parent = ModelChoiceField( label=_('Parent set'),
        queryset=PlanSet.objects.all(), disabled = True, required = False,
        help_text = _('Can be changed only by staff in admin'))

    def __init__(self, **kwargs):
        super(PlanSetUpdateForm, self).__init__(**kwargs)
        #filter plan queryset
        self.fields['plans'].queryset = Plan.objects.filter(build_id=self.initial['build'])

    class Meta:
        model = PlanSet
        fields = ('build', 'parent', 'title', 'intro', 'plans')