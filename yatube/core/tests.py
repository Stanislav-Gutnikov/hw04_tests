from django.test import TestCase


class TestCustomErrorPages(TestCase):

    def test_custom_404(self):
        url_invalid = '/some_invalid_url_404/'
        response = self.client.get(url_invalid)
        self.assertTemplateUsed(response, 'core/404.html')
