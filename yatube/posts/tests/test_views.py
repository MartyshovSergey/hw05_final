from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
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
        cache.clear()
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
        cache.clear()
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


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_cache_index(self):
        """Проверка кэша для index."""
        response = CacheViewsTest.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=CacheViewsTest.author,
        )
        response_old = CacheViewsTest.authorized_client.get(
            reverse('posts:index')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = CacheViewsTest.authorized_client.get(
            reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)

        cls.user_fol = User.objects.create_user(
            username='test_user_follow'
        )
        cls.authorized_user_fol_client = Client()
        cls.authorized_user_fol_client.force_login(
            cls.user_fol
        )

        cls.user_unfol = User.objects.create_user(
            username='test_user_unfollow'
        )
        cls.authorized_user_unfol_client = Client()
        cls.authorized_user_unfol_client.force_login(
            cls.user_unfol
        )
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_new_author_post_for_follower(self):
        client = FollowViewsTest.authorized_user_fol_client
        author = FollowViewsTest.author
        group = FollowViewsTest.group
        client.get(
            reverse(
                'posts:profile_follow',
                args=[author.username]
            )
        )
        response_old = client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            1,
            'Не загружается правильное колличество старых постов'
        )
        self.assertIn(
            FollowViewsTest.post,
            old_posts,
            'Старый пост не верен'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            2,
            'Нету нового поста'
        )
        self.assertIn(
            new_post,
            new_posts,
            'Новый пост не верен'
        )

    def test_new_author_post_for_unfollower(self):
        client = FollowViewsTest.authorized_user_unfol_client
        author = FollowViewsTest.author
        group = FollowViewsTest.group
        response_old = client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            0,
            'Не загружается правильное колличество старых постов'
        )
        self.assertNotIn(
            FollowViewsTest.post,
            old_posts,
            'Старый пост не должен загружаться'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            0,
            'Новый пост не должен появляться'
        )
        self.assertNotIn(
            new_post,
            new_posts,
            'Новый пост не должен появляться'
        )
