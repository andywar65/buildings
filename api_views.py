import copy

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.translation import gettext as _

from rest_framework import generics, permissions
from rest_framework_gis import filters

from .models import Building, Plan, PlanSet, DxfImport, City, PhotoStation
from .serializers import *

class ViewDjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    Extend DjangoModelPermissions to GET requests.
    """
    def __init__(self):
        # you need deepcopy when you inherit a dictionary type
        self.perms_map = copy.deepcopy(self.perms_map)
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']

class IsBuildingVisitor(permissions.BasePermission):
    """
    User test permission. If user is in 'Building Guest' permission group, he
    must be Building visitor.
    """
    def has_permission(self, request, view):
        is_guest = request.user.groups.filter(name='Building Guest').exists()
        if is_guest:
            return request.user == view.build.visitor
        else:
            return True

class BuildingsListApiView(generics.ListAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer

class PlanSetRetrieveApiView(generics.RetrieveAPIView):
    queryset = PlanSet.objects.all()
    permission_classes = [ViewDjangoModelPermissions, IsBuildingVisitor]
    serializer_class = PlanSetSerializer

    def setup(self, request, *args, **kwargs):
        super(PlanSetRetrieveApiView, self).setup(request, *args, **kwargs)
        self.planset = get_object_or_404( PlanSet, id = self.kwargs['pk'] )
        self.build = self.planset.build

class BuildingRetrieveApiView(generics.RetrieveAPIView):
    queryset = Building.objects.all()
    permission_classes = [ViewDjangoModelPermissions, IsBuildingVisitor]
    serializer_class = BuildingSerializer

    def setup(self, request, *args, **kwargs):
        super(BuildingRetrieveApiView, self).setup(request, *args, **kwargs)
        self.build = get_object_or_404( Building, id = self.kwargs['pk'] )

class BuildingCreateApiView(generics.CreateAPIView):
    queryset = Building.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    serializer_class = BuildingLatLongSerializer

class CityListApiView(generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class CityCreateApiView(generics.CreateAPIView):
    queryset = City.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    serializer_class = CityLatLongSerializer

class DxfImportsApiView(generics.ListAPIView):
    bbox_filter_field = "geom"
    filter_backends = (filters.InBBoxFilter,)
    queryset = DxfImport.objects.all()
    serializer_class = DxfImportSerializer
    bbox_filter_include_overlapping = True

class DxfImportsByPlanApiView(generics.ListAPIView):
    serializer_class = DxfImportSerializer
    permission_classes = [ViewDjangoModelPermissions, IsBuildingVisitor]

    def setup(self, request, *args, **kwargs):
        super(DxfImportsByPlanApiView, self).setup(request, *args, **kwargs)
        self.plan = get_object_or_404( Plan, id = self.kwargs['pk'] )
        self.build = self.plan.build

    def get_queryset(self):
        queryset = DxfImport.objects.filter(plan_id=self.plan.id)
        return queryset

class DxfImportsByStationApiView(generics.ListAPIView):
    serializer_class = DxfImportStationSerializer
    permission_classes = [ViewDjangoModelPermissions, IsBuildingVisitor]

    def setup(self, request, *args, **kwargs):
        super(DxfImportsByStationApiView, self).setup(request, *args, **kwargs)
        self.stat = get_object_or_404( PhotoStation, id = self.kwargs['pk'] )
        self.build = self.stat.build

    def get_queryset(self):
        plans = self.build.building_plan.all().values_list('id', flat=True)
        queryset = DxfImport.objects.filter(plan_id__in=plans)
        return queryset

class StationsByPlanApiView(generics.ListAPIView):
    serializer_class = PhotoStationSerializer
    permission_classes = [ViewDjangoModelPermissions, IsBuildingVisitor]

    def setup(self, request, *args, **kwargs):
        super(StationsByPlanApiView, self).setup(request, *args, **kwargs)
        self.plan = get_object_or_404( Plan, id = self.kwargs['pk'] )
        self.build = self.plan.build

    def get_queryset(self):
        queryset = PhotoStation.objects.filter(plan_id=self.plan.id)
        return queryset

class CameraApiView(generics.RetrieveAPIView):
    queryset = PhotoStation.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [ViewDjangoModelPermissions, IsBuildingVisitor]

    def setup(self, request, *args, **kwargs):
        super(CameraApiView, self).setup(request, *args, **kwargs)
        self.stat = get_object_or_404( PhotoStation, id = self.kwargs['pk'] )
        self.build = self.stat.build
