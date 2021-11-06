from rest_framework_gis import serializers

from .models import DxfImport

class DxfImportSerializer(serializers.GeoFeatureModelSerializer):
    """DxfImport full res GeoJSON serializer."""

    class Meta:
        fields = ("id", "layer")
        geo_field = "geom"
        model = DxfImport
