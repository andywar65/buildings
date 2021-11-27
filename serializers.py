from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from .models import DxfImport, Building, City

class DxfImportSerializer(gis_serializers.GeoFeatureModelSerializer):
    """DxfImport GeoJSON serializer."""

    class Meta:
        fields = ("id", "layer", "color_field", )
        geo_field = "geometry"
        model = DxfImport

class BuildingSerializer(gis_serializers.GeoFeatureModelSerializer):
    """Building GeoJSON serializer."""
    path = serializers.ReadOnlyField(source='get_normal_path')
    image_path = serializers.ReadOnlyField(source='image_medium_version_path')

    class Meta:
        fields = ("id", "path", "title", "intro", "image_path", )
        geo_field = "location"
        model = Building

class CitySerializer(gis_serializers.GeoFeatureModelSerializer):
    """City GeoJSON serializer."""

    class Meta:
        fields = ("id", "zoom", )
        geo_field = "location"
        model = City
