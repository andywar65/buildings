from rest_framework import routers

from .api_views import *

router = routers.DefaultRouter()
router.register("hi", ComuniViewSet)
router.register("lo", ComuniLoViewSet)

urlpatterns = router.urls
