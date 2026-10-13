from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from core.models import Organization, OrganizationMembership, Company, CompanyMembership, Branch

class EnterpriseMultiCompanyTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.user=User.objects.create_user(username='owner',password='pass12345',email='owner@example.com')
        self.other=User.objects.create_user(username='other',password='pass12345',email='other@example.com')
        self.org1=Organization.objects.create(name='Org One',slug='org-one',code='ORG-1')
        self.org2=Organization.objects.create(name='Org Two',slug='org-two',code='ORG-2')
        self.c1=Company.objects.create(organization=self.org1,name='Company One',slug='company-one',code='AP-1')
        self.c2=Company.objects.create(organization=self.org2,name='Company Two',slug='company-two',code='AP-2')
        CompanyMembership.objects.create(user=self.user,company=self.c1,role='DIRECTOR',status='ACTIVE')
        CompanyMembership.objects.create(user=self.other,company=self.c2,role='DIRECTOR',status='ACTIVE')
        OrganizationMembership.objects.create(user=self.user,organization=self.org1,role='OWNER',status='ACTIVE')
        OrganizationMembership.objects.create(user=self.other,organization=self.org2,role='OWNER',status='ACTIVE')
        self.client=Client()
        self.client.login(username='owner',password='pass12345')

    def test_cross_org_switch_is_forbidden(self):
        r=self.client.post('/api/v1/enterprise/switch/',{'organization_id':self.org2.id},content_type='application/json')
        self.assertEqual(r.status_code,403)

    def test_branch_is_company_scoped(self):
        self.client.session['active_org_id']=self.org1.id
        self.client.session['active_company_id']=self.c1.id
        self.client.session.save()
        r=self.client.get('/api/v1/enterprise/branches/')
        self.assertEqual(r.status_code,200)
        self.assertEqual([x['company_id'] for x in r.json()['results']],[])
        # branches endpoint never exposes a branch from another organization.
        Branch.objects.create(company=self.c1,name='HQ',code='HQ')
        r=self.client.get('/api/v1/enterprise/branches/')
        self.assertEqual(r.json()['count'],1)
        self.assertEqual(r.json()['results'][0]['company_id'],self.c1.id)
