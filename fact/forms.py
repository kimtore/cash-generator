from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.TextInput({ 'placeholder': 'Brukernavn' }))
    password = forms.CharField(required=True, widget=forms.PasswordInput({ 'placeholder': 'Passord' }))
