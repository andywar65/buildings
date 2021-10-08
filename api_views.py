from rest_framework import viewsets
from rest_framework_gis import filters

from .models import Comuni
from .serializers import *


class ComuniViewSet(viewsets.ReadOnlyModelViewSet):
    """Comuni view set."""

    bbox_filter_field = "geom"
    filter_backends = (filters.InBBoxFilter,)
    queryset = Comuni.objects.all()
    serializer_class = ComuniSerializer
    bbox_filter_include_overlapping = True

class ComuniLoViewSet(viewsets.ReadOnlyModelViewSet):
    """Comuni view set low resolution.
    Probably can be merged with ComuniViewSet"""

    bbox_filter_field = "geom_lo"
    filter_backends = (filters.InBBoxFilter,)
    queryset = Comuni.objects.all()
    serializer_class = ComuniLoSerializer
    bbox_filter_include_overlapping = True
