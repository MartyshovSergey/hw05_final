from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        '''Проверяем, что у моделей корректно работает __str__.'''
        str_testing = {
            self.post: self.post.text[:15],
            self.group: self.group.title,
        }
        for value, expected_value in str_testing.items():
            with self.subTest(value=value):
                self.assertEqual(str(value), expected_value)

    def test_verbose_name(self):
        '''тест verbose_name'''
        verbose_names = {
            'text': 'Текст',
            'group': 'Группа',
        }
        for field, expected_value in verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_title_help_text(self):
        '''Проверка заполнения help_text'''
        field_help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Введите текст поста'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value
                )
