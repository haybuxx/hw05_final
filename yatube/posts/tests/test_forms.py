from http import HTTPStatus
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from ..models import Group, Post, Comment
from ..forms import PostForm
import shutil
import tempfile

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth'),
            text='Тестовая запись для создания 1 поста',
            group=cls.group)

        cls.comment = Comment.objects.create(
            author=User.objects.create_user(username='man'),
            text='Текст комментария',
            post=cls.post)

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        form_data = {
            'text': 'Данные из формы',
            'author': self.user,

        }
        count_comment = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={
                        'post_id': self.post.pk
                    }),
            data=form_data,
            follow=True,
        )
        self.assertTrue(Comment.objects.filter(
                        text=form_data['text'],
                        author=self.user
                        ).exists())
        self.assertEqual(Comment.objects.count(), count_comment + 1)
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.pk}))

    def test_create_post(self):
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.pk
        }
        count_posts = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertTrue(Post.objects.filter(
                        text=form_data['text'],
                        group=form_data['group'],
                        author=self.user
                        ).exists())
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': 'auth'}))

    def test_create_post_not_authorized(self):
        form_data = {
            'text': 'Текст',
            'group': 'Группа'
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
                         text='Текст'
                         ).exists())

    def test_edit_post(self):
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.pk
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': self.post.pk
                    }),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.post.pk)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_2.text, form_data['text'])
        self.assertEqual(post_2.group.pk, form_data['group'])

    def test_edit_post_not_authorized(self):
        form_data = {'text': 'Новый текст',
                     'group': self.group.pk,
                     }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        obj = self.post
        obj.refresh_from_db()
        self.assertNotEqual(obj.text, form_data['text'])
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_no_edit_post_not_author(self):
        posts_count = Post.objects.count()
        form_data = {'text': 'Новый текст',
                     'group': self.group,
                     'author': 'Новый автор'}
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        post = Post.objects.get(id=self.post.pk)
        checked_post = {'text': post.text,
                        'group': post.group,
                        'author': post.author}
        self.assertNotEqual(form_data, checked_post)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error_name2 = 'Поcт добавлен в базу данных по ошибке'
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            error_name2)

    def test_create_post_with_picture(self):
        posts_count = Post.objects.count()
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
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': f'{self.user.username}'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )
