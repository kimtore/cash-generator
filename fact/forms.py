from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.TextInput({ 'placeholder': 'Brukernavn' }))
    password = forms.CharField(required=True, widget=forms.PasswordInput({ 'placeholder': 'Passord' }))

class OptionForm(forms.Form):
    bank_account_number = forms.CharField(required=False)
    bank_iban = forms.CharField(required=False)
    bank_swift_bic = forms.CharField(required=False)
    bank_address = forms.CharField(widget=forms.Textarea, required=False)
    payment_text = forms.CharField(widget=forms.Textarea, required=False)
