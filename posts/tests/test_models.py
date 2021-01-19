from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=User.objects.create_user("Gelya")
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug"
        )

    def test_verbose_name(self):
        post = PostsModelTest.post
        field_verboses = {
            "text": "Текст поста",
            "group": "Группа",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        post = PostsModelTest.post
        field_help_texts = {
            "text": "Текст новой записи",
            "group": "Укажите группу",
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )

    def test_str_is_equal_to_text(self):
        post = PostsModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_str_is_equal_to_title(self):
        group = PostsModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
