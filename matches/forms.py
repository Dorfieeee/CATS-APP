from django.forms import ModelForm, TextInput, Textarea, CheckboxInput, Select
from .models import Match

widgets = {
            'title': TextInput(attrs={
                'placeholder': 'Jméno události',
                'value': 'CATS CUP',
            }),
            'start_at': TextInput(attrs={
                'placeholder': 'Datum cas [YYYY-MM-DD HH-MM-SS]',
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


class MatchCreateForm(ModelForm):
    class Meta:
        model = Match
        fields = ['title', 'start_at', 'description', 'completed', 'maps', 'game']
        widgets = widgets

class MatchUpdateForm(ModelForm):
    class Meta:
        model = Match
        fields = ['title', 'start_at', 'description', 'completed', 'maps', 'leaders', 'participants', 'game']
        widgets = widgets
