from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class LoginViewTests(TestCase):
    def setUp(self):
        # Ensure a Site exists and a SocialApp for google is present
        self.site = Site.objects.get_or_create(pk=getattr(settings, 'SITE_ID', 1))[0]
        app = SocialApp.objects.create(provider='google', name='Google', client_id='x', secret='y')
        app.sites.add(self.site)

    def test_login_page_renders(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)
        # Page should include form and our site title
        self.assertContains(resp, 'Log in')

    def test_provider_link_present_on_login(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)
        # allauth provider link should be present
        self.assertContains(resp, '/accounts/google/login/')

    def test_provider_confirmation_page(self):
        url = '/accounts/google/login/?process=login'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Sign In Via Google')
