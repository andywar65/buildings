from django.urls import path

from .api_views import *

app_name = 'build_api'
urlpatterns = [
    path('dxf/', DxfImportsApiView.as_view(), ),
    path('dxf/by-plan/<pk>/', DxfImportsByPlanApiView.as_view(), ),
]
