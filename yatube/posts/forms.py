from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Введите текст поста',
                  'group': 'Группа к которой будет относиться пост'
                  }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария.'
        }
        help_texts = {
            'text': 'Напишите сюда текст комментария.'
        }
