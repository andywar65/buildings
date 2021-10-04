from rest_framework_gis import serializers

from .models import Comuni


class ComuniSerializer(serializers.GeoFeatureModelSerializer):
    """Comuni GeoJSON serializer."""

    class Meta:
        """Comuni serializer meta class."""

        fields = ("id", "comune_com")
        geo_field = "geom"
        model = Comuni
