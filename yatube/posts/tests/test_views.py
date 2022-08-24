from django import forms
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
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

    def test_index_group_profile_show_correct_context(self):
        """index, group, profile с верным context'ом"""
        context = [
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug})),
            self.authorized_client.get(reverse(
                'posts:profile', kwargs={'username': self.post.author})),
        ]
        for response in context:
            first_object = response.context['page_obj'][0]
            context_objects = {
                self.post.author: first_object.author,
                self.post.text: first_object.text,
                self.post.image: first_object.image,
                self.group.slug: first_object.group.slug,
                self.post.id: first_object.id,
            }
            for reverse_name, response_name in context_objects.items():
                with self.subTest(reverse_name=reverse_name):
                    self.assertEqual(response_name, reverse_name)

    def test_detail_page_correct_context(self):
        """Шаблон post_detail сформирован с неправильным контекстом."""
        reverse_name = reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{self.post.id}'}
        )
        response = self.authorized_client.get(reverse_name)
        first_object = response.context['post']
        context_objects = {
            self.post.author: first_object.author,
            self.post.text: first_object.text,
            self.post.image: first_object.image,
            self.group.slug: first_object.group.slug,
            self.post.id: first_object.id,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_create_use_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_use_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': f'{self.post.id}'}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expect in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expect)

    def test_new_post_with_group_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        new_post_text = first_object.text
        new_post_id = first_object.id
        new_post_group = first_object.group.slug
        self.assertEqual(new_post_text, self.post.text)
        self.assertEqual(new_post_id, self.post.id)
        self.assertEqual(new_post_group, self.group.slug)

    def test_new_post_with_group_group_posts(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        ))
        first_object = response.context['page_obj'][0]
        new_post_text = first_object.text
        new_post_id = first_object.id
        new_post_group = first_object.group.slug
        self.assertEqual(new_post_text, self.post.text)
        self.assertEqual(new_post_id, self.post.id)
        self.assertEqual(new_post_group, self.group.slug)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = PostPagesTests.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=PostPagesTests.author,
        )
        response_old = PostPagesTests.authorized_client.get(
            reverse('posts:index')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = PostPagesTests.authorized_client.get(reverse('index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')


class PaginatorViewsTest(TestCase):
    """Тест Paginator'а на страницах index, group_posts, profile."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='slug',
            description='Тестовая информация о группе'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Тестовый пост {i}'
            )
        cls.url_names = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_posts',
                kwargs={'slug': cls.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ),
        }

    def test_first_page_have_10_posts(self):
        '''Тест: 10 постов на 1й странице'''
        for name, address in self.url_names.items():
            with self.subTest(name=name):
                response = self.client.get(address)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_have_3_posts(self):
        '''Тест: 3 поста на 2й странице'''
        for name, address in self.url_names.items():
            with self.subTest(name=name):
                response = self.client.get(address + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
