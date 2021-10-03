from django.views.generic.base import TemplateView


class ComuniMapView(TemplateView):
    """Comuni map view."""

    template_name = "buildings\comuni_map.html"
