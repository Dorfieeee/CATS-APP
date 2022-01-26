from django.forms import ModelForm, TextInput, Textarea, CheckboxInput, Select
from .models import Match


class MatchCreateForm(ModelForm):
    class Meta:
        model = Match
        fields = ['title', 'start_at', 'description', 'completed', 'maps', 'leaders', 'game', 'participants']
        widgets = {
            'title': TextInput(attrs={
                'placeholder': 'Jméno události',
                'value': 'CATS CUP',
            }),
            'start_at': TextInput(attrs={
                'placeholder': 'Datum time [YYYY-MM-DD HH-MM-SS]',
                'autocomplete': 'off',
            }),
            'description': Textarea(attrs={
                'placeholder': 'Zde zděl nějaké údaje o dané události'
            }),
            'completed': CheckboxInput(attrs={
                'class': 'ui checkbox',
            }),
            'game': Select(attrs={
                'class': 'ui dropdown',
            }),
        }

