from django.forms import ModelForm
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'group': 'Группа', 'text': 'Текст поста'}
        help_texts = {'group': 'Группа, к которой будет относиться пост',
                      'text': 'Текст нового поста'}
        fields = ['text', 'group', 'image']

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}
