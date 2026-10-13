"""Lightweight tenancy regression tests. Run with: python manage.py test core.tests_multicompany"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from core.models import Company, CompanyMembership, UserProfile, Vehicle

class MultiCompanyIsolationTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.user=User.objects.create_user('multi','multi@example.com','pass12345')
        self.a=Company.objects.create(name='Alpha Logistics')
        self.b=Company.objects.create(name='Beta Logistics')
        UserProfile.objects.create(user=self.user,company=self.a,role=UserProfile.ROLE_DIRECTOR,full_name='Multi User')
        CompanyMembership.objects.create(user=self.user,company=self.a,role='DIRECTOR',is_default=True)
        CompanyMembership.objects.create(user=self.user,company=self.b,role='MANAGER')
        Vehicle.objects.create(company=self.a,number='01A111AA',model='ISUZU')
        Vehicle.objects.create(company=self.b,number='01B222BB',model='ISUZU')
        self.client=Client(); self.client.login(username='multi',password='pass12345')

    def test_default_company_isolation(self):
        r=self.client.get('/api/v1/vehicles/')
        self.assertEqual(r.status_code,200)
        self.assertEqual([x['number'] for x in r.json()['results']],['01A111AA'])

    def test_switch_company_changes_tenant_context(self):
        r=self.client.post('/api/v1/companies/switch/',data='{"company_id":%d}'%self.b.id,content_type='application/json')
        self.assertEqual(r.status_code,200)
        r=self.client.get('/api/v1/vehicles/')
        self.assertEqual([x['number'] for x in r.json()['results']],['01B222BB'])

    def test_cross_tenant_switch_is_rejected(self):
        User=get_user_model(); other=User.objects.create_user('outsider','out@example.com','pass12345')
        UserProfile.objects.create(user=other,company=self.a,role=UserProfile.ROLE_MANAGER)
        CompanyMembership.objects.create(user=other,company=self.a,role='MANAGER')
        c=Client(); c.login(username='outsider',password='pass12345')
        r=c.post('/api/v1/companies/switch/',data='{"company_id":%d}'%self.b.id,content_type='application/json')
        self.assertEqual(r.status_code,403)
