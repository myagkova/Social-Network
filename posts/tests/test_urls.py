from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="GelyaM")
        cls.user_new = User.objects.create(username="Hans")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_guest_client(self):
        url_dict = {
            "/": 200,
            "/group/test-slug/": 200,
            "/GelyaM/": 200,
            f"/GelyaM/{self.post.id}/": 200,
            f"/GelyaM/{self.post.id}/edit/": 302,
            "/group/slug_new/": 404,
            f"/GelyaM/{self.post.id}/comment/": 302
        }
        for url, response_code in url_dict.items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, response_code)

    def test_autorized_client(self):
        url_dict = {
            "/": 200,
            "/group/test-slug/": 200,
            "/new/": 200,
            "/GelyaM/": 200,
            f"/GelyaM/{self.post.id}/": 200,
            f"/GelyaM/{self.post.id}/edit/": 200,
            "/group/slug_new/": 404,
            f"/GelyaM/{self.post.id}/comment/": 302
        }
        for url, response_code in url_dict.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, response_code)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            "index.html": "/",
            "group.html": "/group/test-slug/",
            "posts/new.html": "/new/",
            "posts/profile.html": "/GelyaM/",
            "posts/post.html": f"/GelyaM/{self.post.id}/",
            "posts/new.html": f"/GelyaM/{self.post.id}/edit/"
        }
        for template, reverse_name in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_guest_redirect(self):
        response = self.guest_client.get(f"/GelyaM/{self.post.id}/edit/")
        self.assertRedirects(
            response, f"/auth/login/?next=/GelyaM/{self.post.id}/edit/",
            status_code=302, target_status_code=200
        )

    def test_new_post_guest_redirect(self):
        response = self.guest_client.get("/new/")
        self.assertRedirects(
            response, "/auth/login/?next=/new/",
            status_code=302, target_status_code=200
        )

    def test_post_edit_not_author_redirect(self):
        self.authorized_client.force_login(self.user_new)
        response = self.authorized_client.get(f"/GelyaM/{self.post.id}/edit/")
        self.assertRedirects(response, f"/GelyaM/{self.post.id}/",
                             status_code=302, target_status_code=200)
