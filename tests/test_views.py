from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from bimblog.models import Building, BuildingPlan, PhotoStation, StationImage
from users.models import User

@override_settings(USE_I18N=False)#not working
@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT / 'temp'))
class BuildingViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        print("Test bimblog views")
        noviewer = User.objects.create_user(username='noviewer',
            password='P4s5W0r6')
        viewer = User.objects.create_user(username='viewer',
            password='P4s5W0r6')
        adder = User.objects.create_user(username='adder',
            password='P4s5W0r6')
        permissions = Permission.objects.filter(
            codename__in=['view_building', 'view_buildingplan',
            'view_photostation', 'view_stationimage'])
        for p in permissions:
            viewer.user_permissions.add(p)
        group = Group.objects.get(name='Building Manager')
        adder.groups.add(group)

    def setUp(self):
        img_path = Path(settings.STATIC_ROOT /
            'bimblog/images/image.jpg')
        with open(img_path, 'rb') as f:
            content = f.read()
        build = Building.objects.create(title='Building',
            image=SimpleUploadedFile('image.jpg', content, 'image/jpg'))
        build2 = Building.objects.create(title='Building 2',
            image=SimpleUploadedFile('image2.jpg', content, 'image/jpg'))
        dxf_path = Path(settings.STATIC_ROOT /
            'bimblog/dxf/sample.dxf')
        with open(dxf_path, 'rb') as d:
            content_d = d.read()
        BuildingPlan.objects.create(build=build, title='Plan 1',
            file=SimpleUploadedFile('plan1.dxf', content_d, 'text/dxf'))
        stat = PhotoStation.objects.create(build=build, title='Station')
        PhotoStation.objects.create(build=build2, title='Station 2')
        StationImage.objects.create(stat_id=stat.id,
            image=SimpleUploadedFile('image3.jpg', content, 'image/jpg'),
            date=datetime.strptime('2020-05-09 12:00:00',
                '%Y-%m-%d %H:%M:%S'))

    def tearDown(self):
        """Checks existing files, then removes them"""
        path = Path(settings.MEDIA_ROOT /
            'uploads/buildings/images/')
        list = [e for e in path.iterdir() if e.is_file()]
        for file in list:
            Path(file).unlink()
        path = Path(settings.MEDIA_ROOT /
            'uploads/buildings/plans/dxf/')
        list = [e for e in path.iterdir() if e.is_file()]
        for file in list:
            Path(file).unlink()

    def test_list_and_detail_status_code_forbidden(self):
        print("\n-Test bimblog forbidden")
        self.client.post(reverse('front_login'), {'username':'noviewer',
            'password':'P4s5W0r6'})
        print("--Test building list forbidden")
        response = self.client.get(reverse('bimblog:building_list'))
        self.assertEqual(response.status_code, 403)
        print("--Test building detail forbidden")
        response = self.client.get(reverse('bimblog:building_detail',
            kwargs={'slug': 'building'}))
        self.assertEqual(response.status_code, 403)
        print("--Test station detail forbidden")
        response = self.client.get(reverse('bimblog:station_detail',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 403)
        print("--Test image day forbidden")
        response = self.client.get(reverse('bimblog:image_day',
            kwargs={'slug': 'building', 'year': 2020, 'month': 5, 'day': 9}))
        self.assertEqual(response.status_code, 403)

    def test_list_and_detail_status_code_ok(self):
        print("\n-Test bimblog ok")
        self.client.post(reverse('front_login'), {'username':'viewer',
            'password':'P4s5W0r6'})
        print("--Test building list ok")
        response = self.client.get(reverse('bimblog:building_list'))
        self.assertEqual(response.status_code, 200)
        print("--Test building detail ok")
        response = self.client.get(reverse('bimblog:building_detail',
            kwargs={'slug': 'building'}))
        self.assertEqual(response.status_code, 200)
        print("--Test station detail ok")
        response = self.client.get(reverse('bimblog:station_detail',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 200)
        print("--Test image day ok")
        response = self.client.get(reverse('bimblog:image_day',
            kwargs={'slug': 'building', 'year': 2020, 'month': 5, 'day': 9}))
        self.assertEqual(response.status_code, 200)

    def test_create_status_code_forbidden(self):
        print("\n-Test bimblog create forbidden")
        self.client.post(reverse('front_login'), {'username':'viewer',
            'password':'P4s5W0r6'})
        print("--Test building create forbidden")
        response = self.client.get(reverse('bimblog:building_create'))
        self.assertEqual(response.status_code, 403)
        print("--Test buildingplan create forbidden")
        response = self.client.get(reverse('bimblog:buildingplan_create',
            kwargs={'slug': 'building'}))
        self.assertEqual(response.status_code, 403)
        print("--Test photo station create forbidden")
        response = self.client.get(reverse('bimblog:station_create',
            kwargs={'slug': 'building'}))
        self.assertEqual(response.status_code, 403)
        print("--Test image create forbidden")
        response = self.client.get(reverse('bimblog:image_add',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 403)

    def test_create_status_code_ok(self):
        print("\n-Test bimblog create ok")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        print("--Test building create ok")
        response = self.client.get(reverse('bimblog:building_create'))
        self.assertEqual(response.status_code, 200)
        print("--Test buildingplan create ok")
        response = self.client.get(reverse('bimblog:buildingplan_create',
            kwargs={'slug': 'building'}))
        self.assertEqual(response.status_code, 200)
        print("--Test station create ok")
        response = self.client.get(reverse('bimblog:station_create',
            kwargs={'slug': 'building'}))
        self.assertEqual(response.status_code, 200)
        print("--Test image create ok")
        response = self.client.get(reverse('bimblog:image_add',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 200)

    def test_update_status_code_forbidden(self):
        print("\n-Test bimblog update forbidden")
        self.client.post(reverse('front_login'), {'username':'viewer',
            'password':'P4s5W0r6'})
        stat = PhotoStation.objects.get(slug='station')
        image = StationImage.objects.get(stat_id=stat.id)
        print("--Test building update forbidden")
        response = self.client.get(reverse('bimblog:building_change',
            kwargs={'slug': 'building' }))
        self.assertEqual(response.status_code, 403)
        print("--Test building plan update forbidden")
        response = self.client.get(reverse('bimblog:buildingplan_change',
            kwargs={'build_slug': 'building', 'plan_slug': 'plan-1-0'}))
        self.assertEqual(response.status_code, 403)
        print("--Test station update forbidden")
        response = self.client.get(reverse('bimblog:station_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 403)
        print("--Test image update forbidden")
        response = self.client.get(reverse('bimblog:image_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'station',
            'pk': image.id}))
        self.assertEqual(response.status_code, 403)

    def test_update_status_code_ok(self):
        print("\n-Test bimblog update ok")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        stat = PhotoStation.objects.get(slug='station')
        image = StationImage.objects.get(stat_id=stat.id)
        print("--Test building update ok")
        response = self.client.get(reverse('bimblog:building_change',
            kwargs={'slug': 'building' }))
        self.assertEqual(response.status_code, 200)
        print("--Test building plan update ok")
        response = self.client.get(reverse('bimblog:buildingplan_change',
            kwargs={'build_slug': 'building', 'plan_slug': 'plan-1-0'}))
        self.assertEqual(response.status_code, 200)
        print("--Test station update ok")
        response = self.client.get(reverse('bimblog:station_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 200)
        print("--Test image update ok")
        response = self.client.get(reverse('bimblog:image_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'station',
            'pk': image.id}))
        self.assertEqual(response.status_code, 200)

    def test_delete_status_code_forbidden(self):
        print("\n-Test bimblog delete forbidden")
        self.client.post(reverse('front_login'), {'username':'viewer',
            'password':'P4s5W0r6'})
        stat = PhotoStation.objects.get(slug='station')
        image = StationImage.objects.get(stat_id=stat.id)
        print("--Test building delete forbidden")
        response = self.client.get(reverse('bimblog:building_delete',
            kwargs={'slug': 'building' }))
        self.assertEqual(response.status_code, 403)
        print("--Test building plan delete forbidden")
        response = self.client.get(reverse('bimblog:buildingplan_delete',
            kwargs={'build_slug': 'building', 'plan_slug': 'plan-1-0'}))
        self.assertEqual(response.status_code, 403)
        print("--Test station delete forbidden")
        response = self.client.get(reverse('bimblog:station_delete',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 403)
        print("--Test image delete forbidden")
        response = self.client.get(reverse('bimblog:image_delete',
            kwargs={'build_slug': 'building', 'stat_slug': 'station',
            'pk': image.id}))
        self.assertEqual(response.status_code, 403)

    def test_delete_status_code_ok(self):
        print("\n-Test bimblog delete ok")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        stat = PhotoStation.objects.get(slug='station')
        image = StationImage.objects.get(stat_id=stat.id)
        print("--Test building delete ok")
        response = self.client.get(reverse('bimblog:image_delete',
            kwargs={'build_slug': 'building', 'stat_slug': 'station',
            'pk': image.id}))
        self.assertEqual(response.status_code, 200)
        print("--Test building plan delete ok")
        response = self.client.get(reverse('bimblog:station_delete',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 200)
        print("--Test station delete ok")
        response = self.client.get(reverse('bimblog:buildingplan_delete',
            kwargs={'build_slug': 'building', 'plan_slug': 'plan-1-0'}))
        self.assertEqual(response.status_code, 200)
        print("--Test image delete ok")
        response = self.client.get(reverse('bimblog:building_delete',
            kwargs={'slug': 'building' }))
        self.assertEqual(response.status_code, 200)


    def test_wrong_parent_status_code(self):
        print("\n-Test bimblog wrong parent")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        stat = PhotoStation.objects.get(slug='station')
        image = StationImage.objects.get(stat_id=stat.id)
        print("--Test station detail wrong parent")
        response = self.client.get(reverse('bimblog:station_detail',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 404)
        print("--Test image create wrong parent")
        response = self.client.get(reverse('bimblog:image_add',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 404)
        print("--Test building plan wrong parent")
        response = self.client.get(reverse('bimblog:buildingplan_change',
            kwargs={'build_slug': 'building-2', 'plan_slug': 'plan-1-0'}))
        self.assertEqual(response.status_code, 404)
        print("--Test station change wrong parent")
        response = self.client.get(reverse('bimblog:station_change',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 404)
        print("--Test image change wrong parent")
        response = self.client.get(reverse('bimblog:image_change',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station',
            'pk': image.id}))
        self.assertEqual(response.status_code, 404)
        print("--Test plan delete wrong parent")
        response = self.client.get(reverse('bimblog:buildingplan_delete',
            kwargs={'build_slug': 'building-2', 'plan_slug': 'plan-1-0'}))
        self.assertEqual(response.status_code, 404)
        print("--Test station delete wrong parent")
        response = self.client.get(reverse('bimblog:station_delete',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station'}))
        self.assertEqual(response.status_code, 404)
        print("--Test image delete wrong parent")
        response = self.client.get(reverse('bimblog:image_delete',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station',
            'pk': image.id}))
        self.assertEqual(response.status_code, 404)
        print("--Test image change wrong parent")
        response = self.client.get(reverse('bimblog:image_change',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station-2',
            'pk': image.id}))
        self.assertEqual(response.status_code, 404)
        print("--Test image delete wrong station")
        response = self.client.get(reverse('bimblog:image_delete',
            kwargs={'build_slug': 'building-2', 'stat_slug': 'station-2',
            'pk': image.id}))
        self.assertEqual(response.status_code, 404)

    def test_building_crud_redirect(self):
        print("-Test Building CrUD correct redirection")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        img_path = Path(settings.STATIC_ROOT /
            'bimblog/images/image.jpg')
        with open(img_path, 'rb') as f:
            content = f.read()
        print("--Create building")
        response = self.client.post(reverse('bimblog:building_create'),
            {'title': 'Building 4',
            'image': SimpleUploadedFile('image4.jpg', content, 'image/jpg'),
            'intro': 'foo', 'date': '2020-05-09',
            'address': '', 'lat': 40, 'long': 20, 'zoom': 10},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building-4'})+'?created=Building 4',
            status_code=302,
            target_status_code = 200)#302 is first step of redirect chain
        print("--Create building and add another")
        response = self.client.post(reverse('bimblog:building_create'),
            {'title': 'Building 5',
            'image': SimpleUploadedFile('image5.jpg', content, 'image/jpg'),
            'intro': 'foo', 'date': '2020-05-09',
            'address': '', 'lat': 40, 'long': 20, 'zoom': 10, 'add_another': ''},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_create')+'?created=Building 5',
            status_code=302,
            target_status_code = 200)
        print("--Modify building")
        response = self.client.post(reverse('bimblog:building_change',
            kwargs={'slug': 'building-4'}),
            {'title': 'Building 4',
            'image': '',
            'intro': 'foo', 'date': '2020-05-09',
            'address': 'Here', 'lat': 40, 'long': 20, 'zoom': 10},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building-4'})+'?modified=Building 4',
            status_code=302,
            target_status_code = 200)
        print("--Modify building and add another")
        response = self.client.post(reverse('bimblog:building_change',
            kwargs={'slug': 'building-5'}),
            {'title': 'Building 5',
            'image': '',
            'intro': 'foo', 'date': '2020-05-09',
            'address': 'Here', 'lat': 40, 'long': 20, 'zoom': 10,
            'add_another': ''},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_create')+'?modified=Building 5',
            status_code=302,
            target_status_code = 200)
        print("--Delete building")
        response = self.client.post(reverse('bimblog:building_delete',
            kwargs={'slug': 'building-4'}),
            {'delete': True},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_list')+'?deleted=Building 4',
            status_code=302,
            target_status_code = 200)

    def test_buildingplan_crud_redirect(self):
        print("\n-Test BuildingPlan CrUD correct redirection")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        build = Building.objects.get(slug='building')
        dxf_path = Path(settings.STATIC_ROOT /
            'bimblog/dxf/sample.dxf')
        with open(dxf_path, 'rb') as d:
            content_d = d.read()
        print("--Create building plan")
        response = self.client.post(reverse('bimblog:buildingplan_create',
            kwargs={'slug': 'building'}),
            {'build': build.id, 'title': 'Created plan', 'elev': 3.0,
            'file': SimpleUploadedFile('plan2.dxf', content_d, 'txt/dxf'),
            'refresh': True, 'geometry': '', 'visible': True },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building'})+'?plan_created=Created plan',
            status_code=302,
            target_status_code = 200)#302 is first step of redirect chain
        print("--Create building plan and add another")
        response = self.client.post(reverse('bimblog:buildingplan_create',
            kwargs={'slug': 'building'}),
            {'build': build.id, 'title': 'Created plan add', 'elev': 6.0,
            'file': SimpleUploadedFile('plan3.dxf', content_d, 'txt/dxf'),
            'refresh': True, 'geometry': '', 'visible': True,
            'add_another': '' },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:buildingplan_create',
                kwargs={'slug': 'building'})+'?plan_created=Created plan add',
            status_code=302,
            target_status_code = 200)
        print("--Modify building plan")
        response = self.client.post(reverse('bimblog:buildingplan_change',
            kwargs={'build_slug': 'building', 'plan_slug': 'created-plan-30'}),
            {'build': build.id, 'title': 'Created plan', 'elev': 3.0,
            'file': SimpleUploadedFile('plan4.dxf', content_d, 'txt/dxf'),
            'refresh': True, 'geometry': '', 'visible': True },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building'})+'?plan_modified=Created plan',
            status_code=302,
            target_status_code = 200)
        print("--Modify building plan and add another")
        response = self.client.post(reverse('bimblog:buildingplan_change',
            kwargs={'build_slug': 'building',
            'plan_slug': 'created-plan-add-60'}),
            {'build': build.id, 'title': 'Created plan add', 'elev': 6.0,
            'file': SimpleUploadedFile('plan5.dxf', content_d, 'txt/dxf'),
            'refresh': True, 'geometry': '', 'visible': True },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building'})+'?plan_modified=Created plan add',
            status_code=302,
            target_status_code = 200)
        print("--Delete building plan")
        response = self.client.post(reverse('bimblog:buildingplan_delete',
            kwargs={'build_slug': 'building', 'plan_slug': 'created-plan-30'}),
            {'delete': True},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building'})+'?plan_deleted=Created plan',
            status_code=302,
            target_status_code = 200)

    def test_photostation_crud_redirect(self):
        print("\n-Test PhotoStation CrUD correct redirection")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        build = Building.objects.get(slug='building')
        plan = BuildingPlan.objects.get(slug='plan-1-0')
        print("--Create photo station")
        response = self.client.post(reverse('bimblog:station_create',
            kwargs={'slug': 'building'}),
            {'build': build.id, 'plan': plan.id , 'title': 'Created station',
            'intro': 'Foo', 'lat': 40, 'long': 20 },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building'})+'?stat_created=Created station',
            status_code=302,
            target_status_code = 200)#302 is first step of redirect chain
        print("--Create photo station and add another")
        response = self.client.post(reverse('bimblog:station_create',
            kwargs={'slug': 'building'}),
            {'build': build.id, 'plan': plan.id , 'title': 'Created station add',
            'intro': 'Foo', 'lat': 40, 'long': 20, 'add_another': '' },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:station_create',
                kwargs={'slug': 'building'})+'?stat_created=Created station add',
            status_code=302,
            target_status_code = 200)
        print("--Modify photo station")
        response = self.client.post(reverse('bimblog:station_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'created-station'}),
            {'build': build.id, 'plan': plan.id , 'title': 'Created station',
            'intro': 'Bar', 'lat': 40, 'long': 20 },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:station_detail',
                kwargs={'build_slug': 'building',
                'stat_slug': 'created-station'})+'?stat_modified=Created station',
            status_code=302,
            target_status_code = 200)
        print("--Modify photo station and add another")
        response = self.client.post(reverse('bimblog:station_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'created-station-add'}),
            {'build': build.id, 'plan': plan.id , 'title': 'Created station add',
            'intro': 'Bar', 'lat': 40, 'long': 20, 'add_another': '' },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:station_create',
                kwargs={'slug': 'building'})+'?stat_modified=Created station add',
            status_code=302,
            target_status_code = 200)
        print("--Delete photo station")
        response = self.client.post(reverse('bimblog:station_delete',
            kwargs={'build_slug': 'building', 'stat_slug': 'created-station'}),
            {'delete': True},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:building_detail',
                kwargs={'slug': 'building'})+'?stat_deleted=Created station',
            status_code=302,
            target_status_code = 200)

    def test_stationimage_crud_redirect(self):
        print("\n-Test StationImage CrUD correct redirection")
        self.client.post(reverse('front_login'), {'username':'adder',
            'password':'P4s5W0r6'})
        stat = PhotoStation.objects.get(slug='station')
        img_path = Path(settings.STATIC_ROOT /
            'bimblog/images/image.jpg')
        with open(img_path, 'rb') as f:
            content = f.read()
        print("--Create Image")
        response = self.client.post(reverse('bimblog:image_add',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}),
            {'stat': stat.id, 'date': '2021-01-04',
            'image': SimpleUploadedFile('image6.jpg', content, 'image/jpg'),
            'caption': 'Footy Foo' },
            follow = True)
        img = StationImage.objects.get(caption='Footy Foo')
        self.assertRedirects(response,
            reverse('bimblog:station_detail',
                kwargs={'build_slug': 'building',
                'stat_slug': 'station'})+f'?img_created={img.id}',
            status_code=302,
            target_status_code = 200)#302 is first step of redirect chain
        print("--Create Image and add another")
        response = self.client.post(reverse('bimblog:image_add',
            kwargs={'build_slug': 'building', 'stat_slug': 'station'}),
            {'stat': stat.id, 'date': '2021-01-04',
            'image': SimpleUploadedFile('image7.jpg', content, 'image/jpg'),
            'caption': 'Barry bar', 'add_another': '' },
            follow = True)
        img = StationImage.objects.get(caption='Barry bar')
        self.assertRedirects(response,
            reverse('bimblog:image_add',
                kwargs={'build_slug': 'building',
                'stat_slug': 'station'})+f'?img_created={img.id}',
            status_code=302,
            target_status_code = 200)
        print("--Modify Image")
        response = self.client.post(reverse('bimblog:image_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'station',
            'pk': img.id}),
            {'stat': stat.id, 'date': '2021-01-04',
            'image': SimpleUploadedFile('image8.jpg', content, 'image/jpg'),
            'caption': 'Barry bar' },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:station_detail',
                kwargs={'build_slug': 'building',
                'stat_slug': 'station'})+f'?img_modified={img.id}',
            status_code=302,
            target_status_code = 200)
        print("--Modify Image and add another")
        response = self.client.post(reverse('bimblog:image_change',
            kwargs={'build_slug': 'building', 'stat_slug': 'station',
            'pk': img.id}),
            {'stat': stat.id, 'date': '2021-01-04',
            'image': SimpleUploadedFile('image9.jpg', content, 'image/jpg'),
            'caption': 'Barry bar', 'add_another': '' },
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:image_add',
                kwargs={'build_slug': 'building',
                'stat_slug': 'station'})+f'?img_modified={img.id}',
            status_code=302,
            target_status_code = 200)
        print("--Delete Image")
        response = self.client.post(reverse('bimblog:image_delete',
            kwargs={'build_slug': 'building', 'stat_slug': 'station',
            'pk': img.id}),
            {'delete': True},
            follow = True)
        self.assertRedirects(response,
            reverse('bimblog:station_detail',
                kwargs={'build_slug': 'building',
                'stat_slug': 'station'})+f'?img_deleted={img.id}',
            status_code=302,
            target_status_code = 200)
