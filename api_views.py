from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import generics
from rest_framework_gis import filters

from .models import Plan, DxfImport
from .serializers import *

class DxfImportsApiView(generics.ListAPIView):

    bbox_filter_field = "geom"
    filter_backends = (filters.InBBoxFilter,)
    queryset = DxfImport.objects.all()
    serializer_class = DxfImportSerializer
    bbox_filter_include_overlapping = True

class DxfImportsByPlanApiView(generics.ListAPIView):

    #bbox_filter_field = "geom"
    #filter_backends = (filters.InBBoxFilter,)
    #queryset = DxfImport.objects.all()
    serializer_class = DxfImportSerializer
    #bbox_filter_include_overlapping = True

    def setup(self, request, *args, **kwargs):
        super(DxfImportsByPlanApiView, self).setup(request, *args, **kwargs)
        self.plan = get_object_or_404( Plan, id = self.kwargs['pk'] )
        if self.plan.build.private:
            if not self.request.user.has_perm('buildings.view_dxfimport'):
                raise Http404(_("User can't view DxfImports"))

    def get_queryset(self):
        queryset = DxfImport.objects.filter(plan_id=self.plan.id)
        return queryset
