from rest_framework_gis import serializers

from .models import DxfImport

class DxfImportSerializer(serializers.GeoFeatureModelSerializer):
    """DxfImport GeoJSON serializer."""

    class Meta:
        fields = ("id", "layer", "color_field", )
        geo_field = "geom"
        model = DxfImport
