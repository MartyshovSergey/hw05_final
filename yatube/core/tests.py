from http import HTTPStatus

from django.test import TestCase


class CoreViewTest(TestCase):
    def test_error404_page(self):
        ''' Тестируем доступ страницы 404 и кастомный шаблон. '''
        response = self.client.get('/nonexist-page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
