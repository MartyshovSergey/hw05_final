from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post
from yatube.settings import POSTS_PER_PAGE

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

    @classmethod
    def setUp(self):
        cache.clear()

    def test_index_group_profile_detail_show_correct_context(self):
        ''' index, group, profile, detail с неверным контекстом. '''
        context = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'page_obj',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'post',
        }
        for url, cont_obj in context.items():
            response = self.authorized_client.get(url)
            if cont_obj == 'page_obj':
                first_object = response.context['page_obj'][0]
            else:
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

    def test_post_create_and_post_edit_use_correct_context(self):
        responses = [
            (reverse('posts:post_create')),
            (reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}))
        ]
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for url in responses:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_new_post_with_group_index_and_group_posts(self):
        responses = [
            (reverse('posts:group_posts', kwargs={'slug': self.group.slug})),
            (reverse('posts:index'))
        ]
        for url in responses:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context['page_obj'][0]
                new_post_text = first_object.text
                new_post_id = first_object.id
                new_post_group = first_object.group.slug
                self.assertEqual(new_post_text, self.post.text)
                self.assertEqual(new_post_id, self.post.id)
                self.assertEqual(new_post_group, self.group.slug)


class PaginatorViewsTest(TestCase):
    ''' Тестируем пагинатор на страницах index, group_list, profile. '''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.SECOND_PAGE = 3
        objs = [
            Post(
                author=cls.user,
                group=cls.group,
                text=f'test-post {i}'
            )
            for i in range(cls.SECOND_PAGE + POSTS_PER_PAGE)
        ]
        cls.post = Post.objects.bulk_create(objs=objs)

    def setUp(self):
        self.client = Client()
        self.url_names = {
            'index': reverse('posts:index'),
            'group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
        }
        cache.clear()

    def test_first_page_contains_ten_records(self):
        '''Тест: 10 постов на 1й странице'''
        for name, address in self.url_names.items():
            with self.subTest(name=name):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    POSTS_PER_PAGE
                )

    def test_second_page_contains_three_records(self):
        '''Тест: 3 поста на 2й странице'''
        for name, address in self.url_names.items():
            with self.subTest(name=name):
                response = self.client.get(address + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.SECOND_PAGE
                )


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        post_note = 'Создаем пост'
        Post.objects.create(
            text=post_note,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index_pages(self):
        """Проверяем работу кэша главной страницы."""
        first_response = self.client.get(reverse('posts:index'))
        anoter_post_note = 'Создаем еще один пост'
        Post.objects.create(
            text=anoter_post_note,
            author=self.user
        )
        response_after_post_add = self.client.get(reverse('posts:index'))
        self.assertEqual(
            first_response.content,
            response_after_post_add.content
        )
        cache.clear()
        response_after_cache_clean = self.client.get(reverse('posts:index'))
        self.assertNotEqual(
            first_response.content,
            response_after_cache_clean.content
        )


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
            len(response_old.context.get('page_obj')),
            FollowViewsTest.user_fol.follower.count(),
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
            len(response_new.context.get('page_obj')),
            FollowViewsTest.user_fol.follower.count() + 1,
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
            FollowViewsTest.user_fol.follower.count(),
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
            FollowViewsTest.user_fol.follower.count(),
            'Новый пост не должен появляться'
        )
        self.assertNotIn(
            new_post,
            new_posts,
            'Новый пост не должен появляться'
        )


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='test_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.auth_user)
        cls.author = User.objects.create_user(username='test_author')
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

    def test_add_comment(self):
        ''' Тест добавления коммента к посту. '''
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'test-comment',
        }
        response = self.auth_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        comment_obj = Comment.objects.first()
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],
        ).exists())
        self.assertEqual(comment_obj.author, self.auth_user)
