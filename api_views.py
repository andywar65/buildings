from rest_framework import viewsets
from rest_framework_gis import filters

from .models import Comuni
from .serializers import ComuniSerializer


class ComuniViewSet(viewsets.ReadOnlyModelViewSet):
    """Comuni view set."""

    bbox_filter_field = "geom"
    filter_backends = (filters.InBBoxFilter,)
    queryset = Comuni.objects.all()
    serializer_class = ComuniSerializer
