from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Group, Post
from django.urls import reverse

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
        )
        cls.group = Group.objects.create(
            title=('Тестовый заголовок'),
            slug='slug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.client_enforce_csrf_checks = Client(enforce_csrf_checks=True)
        self.authorized_client.force_login(self.user)

    def test_public_pages(self):
        reverse_group = reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        )
        reverse_user = reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        reverse_post = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        reverse_index = reverse(
            'posts:index'
        )
        urls_list = [
            reverse_index,
            reverse_group,
            reverse_user,
            reverse_post,
        ]
        for urls in urls_list:
            response = self.guest_client.get(urls)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_authorized(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_for_authorized(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            reverse('posts:index'): "posts/index.html",
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostURLTests.group.slug}
            ): "posts/group_list.html",
            reverse('posts:post_create'): "posts/create_post.html",
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ): "posts/profile.html",
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ): "posts/post_detail.html",
            reverse('unexisting_page'): "core/404.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_403(self):
        response = self.client_enforce_csrf_checks.post('/create/')
        self.assertTemplateUsed(response, 'core/403csrf.html')

    def test_page_404(self):
        url_names = [
            '/unexisting_page/',
            f'/posts/{str(77)}/',
            '/group/meow/',
            '/profile/anton/',
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
