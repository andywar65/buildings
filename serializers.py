from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from .models import DxfImport, Building, City, Plan, PlanSet, PhotoStation

class DxfImportSerializer(gis_serializers.GeoFeatureModelSerializer):
    """DxfImport GeoJSON serializer."""
    data = serializers.ReadOnlyField(source='get_area_or_length')

    class Meta:
        fields = ("id", "layer", "color_field", "data", )
        geo_field = "geometry"
        model = DxfImport

class BuildingSerializer(gis_serializers.GeoFeatureModelSerializer):
    """Building GeoJSON serializer."""
    path = serializers.ReadOnlyField(source='get_normal_path')
    image_path = serializers.ReadOnlyField(source='image_medium_version_path')

    class Meta:
        fields = ("id", "path", "title", "intro", "image_path", "zoom")
        geo_field = "location"
        model = Building

class PhotoStationSerializer(gis_serializers.GeoFeatureModelSerializer):
    """PhotoStation GeoJSON serializer."""
    data = serializers.ReadOnlyField(source='map_dictionary')

    class Meta:
        fields = ("data", )
        geo_field = "location"
        model = PhotoStation

class BuildingLatLongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ("image", "title", "intro", "lat", "long", "zoom")

class PlanSetSerializer(serializers.ModelSerializer):
    plans = serializers.ReadOnlyField(source='get_plans_to_serialize')
    class Meta:
        model = PlanSet
        fields = ("id", "plans", )

class CitySerializer(gis_serializers.GeoFeatureModelSerializer):
    """City GeoJSON serializer."""

    class Meta:
        fields = ("id", "zoom", )
        geo_field = "location"
        model = City

class CityLatLongSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("name", "lat", "long", "zoom")
