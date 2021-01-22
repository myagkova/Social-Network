import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User


class PostsModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username="gelya",
            first_name="Angelina",
            last_name="Myagkova"
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание"
        )
        cls.group_new = Group.objects.create(
            title="Новая тестовая группа",
            slug="test-slugnew",
            description="Новое тестовое описание"
        )
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            "index.html": reverse("index"),
            "group.html": reverse("group", kwargs={"slug": "test-slug"}),
            "posts/new.html": reverse("new_post"),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        Post.objects.bulk_create(
            [Post(
                text=str(i),
                author=self.user,
                group=self.group,
                image=uploaded
            ) for i in range(0, 10)]
        )
        response = self.authorized_client.get(reverse("index"))
        post_list = response.context.get("page")
        self.assertQuerysetEqual(
            post_list, Post.objects.all()[:10], transform=lambda x: x
        )

    def test_group_page_show_correct_context(self):
        Post.objects.bulk_create(
            [Post(
                text=str(i),
                author=self.user,
                group=self.group
            ) for i in range(0, 10)]
        )
        response = self.authorized_client.get(
            reverse("group", kwargs={"slug": "test-slug"})
        )
        group = response.context.get("group")
        self.assertEqual(group, self.group)
        post_list = response.context.get("page")
        self.assertEqual(len(post_list), 5)
        self.assertQuerysetEqual(
            post_list, Post.objects.all()[:5], transform=lambda x: x
        )

    def test_post_in_correct_group(self):
        response = self.authorized_client.get(
            reverse("group", kwargs={"slug": "test-slugnew"})
        )
        post = response.context.get("page")
        self.assertEqual(len(post), 0)

    def test_new_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse("new_post"))
        form_fields = {
            "text": forms.CharField,
            "group": forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                "post_edit",
                kwargs={
                    "username": "gelya",
                    "post_id": f"{self.post.id}"
                }
            )
        )
        is_edit = response.context.get("is_edit")
        self.assertTrue(is_edit)
        form_fields = {
            "text": forms.CharField,
            "group": forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_profile_page_show_correct_contex(self):
        Post.objects.bulk_create(
            [Post(
                text=str(i),
                author=self.user,
                group=self.group
            ) for i in range(0, 10)]
        )
        response = self.authorized_client.get(
            reverse(
                "profile", kwargs={
                    "username": "gelya"
                }
            )
        )
        author = response.context.get("author")
        self.assertEqual(author, self.user)
        post_count = response.context.get("post_count")
        self.assertEqual(post_count, 11)
        post_list = response.context.get("page")
        self.assertQuerysetEqual(
            post_list, Post.objects.all()[:5], transform=lambda x: x
        )

    def test_post_view_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                "post",
                kwargs={
                    "username": "gelya",
                    "post_id": f"{self.post.id}"
                }
            )
        )
        author = response.context.get("author")
        self.assertEqual(author, self.user)
        post = response.context.get("post")
        self.assertEqual(post, self.post)
        post_count = response.context.get("post_count")
        self.assertEqual(post_count, 1)

    def test_page_contains_records(self):
        posts = []
        for i in range(0, 15):
            posts.append(Post(
                text=f"Тестовый текст {i}",
                author=self.user,
                group=self.group
            ))
        Post.objects.bulk_create(posts)
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context.get("page").object_list), 10)
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context.get('page').object_list), 6)

    def test_home_page_cache(self):
        response = self.client.get(reverse("index"))
        Post.objects.create(
            text="Text",
            author=self.user,
            group=self.group
        )
        response_new = self.client.get(reverse("index"))
        self.assertEqual(response_new.content, response.content)

    def test_following_users(self):
        new_user = User.objects.create(username="bardem")
        self.assertFalse(
            Follow.objects.filter(author=new_user, user=self.user).exists()
        )
        response = self.authorized_client.post(reverse(
            "profile_follow", kwargs={"username": "bardem"}
        ), follow=True)
        self.assertEqual(response.status_code, 200)
        following = response.context.get("following")
        self.assertTrue(following)
        self.assertTrue(
            Follow.objects.filter(author=new_user, user=self.user).exists()
        )

    def test_unfollowing_users(self):
        new_user = User.objects.create(username="bardem")
        response_follow = self.authorized_client.post(reverse(
            "profile_follow", kwargs={"username": "bardem"}
        ), follow=True)
        following = response_follow.context.get("following")
        self.assertTrue(
            Follow.objects.filter(author=new_user, user=self.user).exists()
        )
        response_unfollow = self.authorized_client.get(reverse(
            "profile_unfollow", kwargs={"username": "bardem"}
        ), follow=True)
        following = response_unfollow.context.get("following")
        self.assertFalse(following)
        self.assertFalse(
            Follow.objects.filter(author=new_user, user=self.user).exists()
        )

    def test_new_post_for_followers(self):
        follower = User.objects.create(username="bardem")
        self.authorized_client.force_login(follower)
        self.authorized_client.get(reverse(
            "profile_follow", kwargs={"username": "gelya"}
        ))
        self.authorized_client.logout()
        self.authorized_client.force_login(self.user)
        Post.objects.create(
            text="Тестовый текст",
            author=self.user
        )
        self.authorized_client.logout()
        self.authorized_client.force_login(follower)
        response = self.authorized_client.get(reverse("follow_index"))
        self.assertEqual(len(response.context.get("page").object_list), 2)
        not_follower = User.objects.create(username="hammer")
        self.authorized_client.logout()
        self.authorized_client.force_login(not_follower)
        response = self.authorized_client.get(reverse("follow_index"))
        self.assertEqual(len(response.context.get("page").object_list), 0)

    def test_comments_for_authorized_client(self):
        new_user = User.objects.create(username="bardem")
        self.authorized_client.force_login(new_user)
        self.authorized_client.post(reverse(
            "add_comment",
            kwargs={"username": self.user.username,
                    "post_id": f"{self.post.id}"}
        ))
        self.assertTrue(
            Comment.objects.filter(
                author=new_user, post_id=f"{self.post.id}").exists()
        )

    def test_comments_for_guest_client(self):
        self.guest_client.post(reverse(
            "add_comment",
            kwargs={"username": self.user.username,
                    "post_id": f"{self.post.id}"}
        ))
        self.assertFalse(
            Comment.objects.filter(
                post_id=f"{self.post.id}").exists()
        )
