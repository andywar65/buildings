from rest_framework import routers

from .api_views import ComuniViewSet

router = routers.DefaultRouter()
router.register(r"", ComuniViewSet)

urlpatterns = router.urls
