from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class PostsUrlsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='slug',
            description='Тестовая информация о группе'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.post.author)

    def test_url_avaliable_to_authorized(self):
        """Страницы доступные авторизованным пользователям"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_available_to_author_post(self):
        """Страница редактирования поста"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_used_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        """При попытке перехода на несуществующую страницу"""
        response = self.client.get('/12312dsf/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Запрос по адресу /posts/{self.post.id}/edit/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.id}/edit/'))

    def test_random_client_redirect_url(self):
        """У не автора поста должен проверяться редирект"""
        response = self.client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.id}/edit/'))
