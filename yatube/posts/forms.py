
from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group']
        labels = {
            'text': 'Текст поста',
            'group': 'Группа, к которой будет относится пост'
        }

        def clean_data(self):
            text = self.cleaned_data['text']
            if not text:
                raise forms.ValidationError('Пост не может быть без текста')
            return text
