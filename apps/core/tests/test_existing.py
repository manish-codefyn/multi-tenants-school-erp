from django.test import SimpleTestCase, RequestFactory
from django.http import Http404
from django.contrib.auth.models import AnonymousUser
from apps.core.views import (
    custom_page_not_found_view,
    custom_error_view,
    custom_permission_denied_view,
    custom_bad_request_view
)

class ErrorPageTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_404_view(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = custom_page_not_found_view(request, exception=Http404("Not Found"))
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.content)

    def test_500_view(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = custom_error_view(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Internal Server Error", response.content)

    def test_403_view(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = custom_permission_denied_view(request, exception=Exception("Forbidden"))
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Denied", response.content)

    def test_400_view(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = custom_bad_request_view(request, exception=Exception("Bad Request"))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Bad Request", response.content)
