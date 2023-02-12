from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
import shutil
import tempfile

User = get_user_model()


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create(username='auth')

        cls.post = Post.objects.create(
            pk=1,
            author=cls.user,
            text='Тестовая запись для создания поста',
            group=Group.objects.create(
                title='Заголовок для тестовой группы',
                slug='slug'),
            image=uploaded)

        cls.postTwo = Post.objects.create(
            pk=2,
            author=cls.user,
            text='Тестовая запись 2 для создания поста',
            group=Group.objects.create(
                title='Заголовок 2 для тестовой группы',
                slug='slug2'),
            image=uploaded)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (reverse('posts:group_posts',
                                              kwargs={'slug': 'slug'})),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': 'auth'}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.pk}),
            'posts/create_post.html':
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),

        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_correct_template(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][1]
        post_image_1 = Post.objects.get(pk=1).image.name
        self.assertEqual(post_image_1, self.post.image.name)
        context_objects = {
            first_object.author.username: self.post.author.username,
            first_object.text: self.post.text,
            first_object.group.title: self.post.group.title,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_group_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_posts',
                                              kwargs={'slug':
                                                      self.post.group.slug
                                                      }))
        first_object = response.context['page_obj'][0]
        post_image_1 = Post.objects.get(pk=1).image.name
        self.assertEqual(post_image_1, self.post.image.name)
        self.assertEqual(self.post.group.title,
                         first_object.group.title)
        self.assertEqual(self.post.group.slug, first_object.group.slug)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username':
                                                      f'{self.user.username}'
                                                      }))
        post_image_1 = Post.objects.get(pk=1).image.name
        self.assertEqual(post_image_1, self.post.image.name)
        first_object = response.context['page_obj'][1]
        self.assertEqual(response.context['author'].username, f'{self.user}')
        self.assertEqual(first_object.text,
                         self.post.text)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.pk}))
        post_image_0 = Post.objects.get(pk=1).image.name
        self.assertEqual(post_image_0, self.post.image.name)
        self.assertEqual(response.context['post1'], self.post.text)

    def test_create_post_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              self.post.pk}))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        response = self.authorized_client.get(reverse('posts:group_posts',
                                              kwargs={'slug': 'slug'}))
        first_object = response.context['page_obj'][0]
        self.assertTrue(self.postTwo.text, first_object.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth',)

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='slug',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse('posts:index'): 'index',
            reverse('posts:group_posts',
                    kwargs={'slug': 'slug'}): 'group_posts',
            reverse('posts:profile', kwargs={'username': 'auth'}): 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_contains_three_posts(self):
        templates_pages_names = {
            reverse("posts:index"):
                'posts/index.html',
            reverse("posts:group_list", kwargs={"slug": self.group.slug}):
                'posts/group_list.html',
            reverse("posts:profile", kwargs={"username": self.user}):
                'posts/profile.html',
        }

        for reverse_name, _ in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                page = 2
                response = self.authorized_client.get(
                    reverse_name,
                    {'page': page}
                )
                self.assertEqual(
                    len(response.context['page_obj']), 3
                )


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower',
                                                      )
        self.user_following = User.objects.create_user(username='following',
                                                       )
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись '
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription(self):
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, self.post.text)
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response,
                               self.post.text)
