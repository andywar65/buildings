from django.urls import path
from django.utils.translation import gettext_lazy as _

from .views import *

app_name = 'buildings'
urlpatterns = [
    path('', BuildingListCreateView.as_view(), name = 'building_list'),
    path('<slug:build_slug>/sets/<slug:set_slug>',
        BuildingDetailView.as_view(), name = 'building_detail'),
    path(_('<slug>/change/'), BuildingUpdateView.as_view(), name = 'building_change'),
    path(_('<slug>/delete/'), BuildingDeleteView.as_view(), name = 'building_delete'),
    path(_('<slug>/plan/add/'), PlanCreateView.as_view(),
        name = 'plan_create'),
    path(_('<slug:build_slug>/plan/<slug:plan_slug>/change/'),
        PlanUpdateView.as_view(), name = 'plan_change'),
    path(_('<slug:build_slug>/plan/<slug:plan_slug>/delete/'),
        PlanDeleteView.as_view(), name = 'plan_delete'),
    path(_('<slug>/station/add/'), PhotoStationCreateView.as_view(),
        name = 'station_create'),
    path(_('<slug:build_slug>/station/<slug:stat_slug>/'),
        StationImageListCreateView.as_view(), name = 'station_detail'),
    path(_('<slug:build_slug>/station/<slug:stat_slug>/change/'),
        PhotoStationUpdateView.as_view(), name = 'station_change'),
    path(_('<slug:build_slug>/station/<slug:stat_slug>/delete/'),
        PhotoStationDeleteView.as_view(), name = 'station_delete'),
    path(_('<slug:build_slug>/stations/<slug:stat_slug>/image/<pk>/change'),
        StationImageUpdateView.as_view(), name = 'image_change'),
    path(_('<slug:build_slug>/stations/<slug:stat_slug>/image/<pk>/delete'),
        StationImageDeleteView.as_view(), name = 'image_delete'),
    path(_('<slug>/stations/<int:year>/<int:month>/<int:day>/'),
        StationImageDayArchiveView.as_view(), name = 'image_day'),
    path(_('<slug>/sets/add/'), PlanSetCreateView.as_view(),
        name = 'planset_create'),
    path(_('<slug>/sets/<pk>/change/'),
        PlanSetUpdateView.as_view(), name = 'planset_change'),
    path(_('<slug>/sets/<pk>/delete/'),
        DisciplineDeleteView.as_view(), name = 'discipline_delete'),
    ]
