from rest_framework import generics
from rest_framework_gis import filters

from .models import DxfImport
from .serializers import *

class DxfImportsApiView(generics.ListAPIView):

    bbox_filter_field = "geom"
    filter_backends = (filters.InBBoxFilter,)
    queryset = DxfImport.objects.all()
    serializer_class = DxfImportSerializer
    bbox_filter_include_overlapping = True
