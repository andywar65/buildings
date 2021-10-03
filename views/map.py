from django.views.generic.base import TemplateView


class ComuniMapView(TemplateView):
    """Markers map view."""

    template_name = "comuni_map.html"
