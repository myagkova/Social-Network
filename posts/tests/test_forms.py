import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="gelya")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug"
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
        cls.form = PostForm()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_form(self):
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small2.jpeg',
            content=small_gif,
            content_type='image/jpeg'
        )
        posts_count = Post.objects.count()
        form_data = {
            "image": uploaded,
            "group": self.group.id,
            "text": "Текст поста",
        }
        self.assertFalse(Post.objects.filter(text=form_data["text"]).exists())
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(
            group=form_data["group"],
            text=form_data["text"]
        ).exists()
        )

    def test_edit_post_form(self):
        posts_count = Post.objects.count()
        form_data = {
            "group": self.group.id,
            "text": "Текст поста",
        }
        response = self.authorized_client.post(
            reverse(
                "post_edit",
                kwargs={
                    "username": "gelya",
                    "post_id": f"{self.post.id}"
                }
            ),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.text, form_data["text"])
        self.assertEqual(self.post.group.id, form_data["group"])
