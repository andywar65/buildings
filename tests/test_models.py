import os
from datetime import datetime

from django.conf import settings
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from bimblog.models import Building, BuildingPlan, PhotoStation, StationImage

@override_settings(USE_I18N=False)
class BuildingModelTest(TestCase):
    """Testing all methods that don't need SimpleUploadedFile"""
    @classmethod
    def setUpTestData(cls):
        build = Building.objects.create(title='Building', )
        Building.objects.create(date=datetime.strptime('2020-05-09', '%Y-%m-%d'))
        stat = PhotoStation.objects.create(build=build, title='Station')

    def test_building_str_method(self):
        build = Building.objects.get(slug='building')
        self.assertEquals(build.__str__(), 'Building')

    def test_building_intro(self):
        build = Building.objects.get(slug='building')
        self.assertEquals(build.intro,
            f'Another Building by {settings.WEBSITE_NAME}!')

    def test_building_maps(self):
        build = Building.objects.get(slug='building')
        self.assertEquals(build.lat, settings.CITY_LAT )
        self.assertEquals(build.long, settings.CITY_LONG )
        self.assertEquals(build.zoom, settings.CITY_ZOOM )

    def test_building_str_method_no_title(self):
        build = Building.objects.get(date='2020-05-09')
        self.assertEquals(build.__str__(), 'Building-09-05-20')

    def test_building_get_full_path(self):
        build = Building.objects.get(slug='building')
        self.assertEquals(build.get_full_path(), '/buildings/building/')

    def test_photostation_str_method(self):
        stat = PhotoStation.objects.get(slug='station')
        self.assertEquals(stat.__str__(), 'Station / Building')

    def test_photostation_intro(self):
        stat = PhotoStation.objects.get(slug='station')
        self.assertEquals(stat.intro,
            f'Another photo station by {settings.WEBSITE_NAME}!')

    def test_station_maps(self):
        stat = PhotoStation.objects.get(slug='station')
        self.assertEquals(stat.lat, stat.build.lat )
        self.assertEquals(stat.long, stat.build.long )

@override_settings(MEDIA_ROOT=os.path.join(settings.MEDIA_ROOT, 'temp'))
class StationImageTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        img_path = os.path.join(settings.STATIC_ROOT,
            'bimblog/images/image.jpg')
        with open(img_path, 'rb') as f:
            content = f.read()
        dxf_path = os.path.join(settings.STATIC_ROOT,
            'bimblog/dxf/sample.dxf')
        with open(dxf_path, 'rb') as d:
            content_d = d.read()
        build = Building.objects.create(title='Building',
            image=SimpleUploadedFile('image.jpg', content, 'image/jpg'))
        BuildingPlan.objects.create(build=build, title='Plan 1',
            file=SimpleUploadedFile('plan1.dxf', content_d, 'text/dxf'))
        stat = PhotoStation.objects.create(build=build, title='Station')
        #we get the same content, but name the image differently
        statimg = StationImage.objects.create(stat_id=stat.id,
            image=SimpleUploadedFile('image2.jpg', content, 'image/jpg'))

    def tearDown(self):
        """Checks existing files, then removes them"""
        try:
            list = os.listdir(os.path.join(settings.MEDIA_ROOT,
                'uploads/buildings/images/'))
        except:
            return
        for file in list:
            os.remove(os.path.join(settings.MEDIA_ROOT,
                f'uploads/buildings/images/{file}'))
        try:
            list = os.listdir(os.path.join(settings.MEDIA_ROOT,
                'uploads/buildings/plans/dxf/'))
        except:
            return
        for file in list:
            os.remove(os.path.join(settings.MEDIA_ROOT,
                f'uploads/buildings/plans/dxf/{file}'))

    def test_buildingplan_str_method(self):
        plan = BuildingPlan.objects.get(slug='plan-1-0')
        self.assertEquals(plan.__str__(), 'Plan 1 | 0.0')

    def test_buildingplan_geometry(self):
        plan = BuildingPlan.objects.get(slug='plan-1-0')
        geometry = [{'type': 'polygon', 'color': '#999999',
        'popup': 'Porticato',
        'coords': [[41.89830800279919, 12.545726001278254],
        [41.89827524195551, 12.545717364542545],
        [41.89823424354996, 12.545635389111553],
        [41.89841413674754, 12.545472980512894],
        [41.89846830605199, 12.54558129087325]]},
        {'type': 'polygon', 'color': '#ffbf00', 'popup': 'Aule tecniche',
        'coords': [[41.89823424354996, 12.545635389111553],
        [41.89802207569236, 12.545211164038943],
        [41.89802550424858, 12.545187689834192],
        [41.89819807177193, 12.5450355472492],
        [41.89823418464156, 12.545107754156103],
        [41.8984160029088, 12.545471295874886]]}]
        self.assertEquals(plan.geometry, geometry)

    def test_building_fb_image(self):
        build = Building.objects.get(slug='building')
        self.assertEquals(build.image, None)
        self.assertEquals(build.fb_image.path, 'uploads/buildings/images/image.jpg')

    def test_stationimage_fb_image(self):
        stat = PhotoStation.objects.get(slug='station')
        image = StationImage.objects.filter(stat_id=stat.id).first()
        self.assertEquals(image.image, None)
        self.assertEquals(image.fb_image.path, 'uploads/buildings/images/image2.jpg')
