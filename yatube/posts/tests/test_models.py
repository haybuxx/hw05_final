from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post, Comment

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Текст комментария',
            post=cls.post)

    def test_models_have_correct_str(self):
        post = PostModelTest.post
        expected_object_name = post.text
        self.assertEqual(expected_object_name, str(post))

        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_comment_exist(self):
        comment = PostModelTest.comment
        expected_object_name = comment.text
        self.assertEqual(expected_object_name, str(comment))
