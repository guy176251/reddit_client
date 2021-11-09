from django import forms

class SubredditForm(forms.Form):
    sub_name = forms.CharField(label='', max_length=100,
                               widget=forms.TextInput(attrs={'placeholder':'Search for subreddit'}))
