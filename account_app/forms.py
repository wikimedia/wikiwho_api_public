# from registration import validators
# from registration.forms import RegistrationFormUniqueEmail

from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, EmailField, Form, forms, CharField, HiddenInput

from account_app.models import Account, User


class AccountForm(ModelForm):
    prefix = 'account'

    class Meta:
        model = Account
        fields = ('affiliation', 'reason', )


class UserForm(ModelForm):
    prefix = 'user'

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', )

    def __init__(self, *args, **kwargs):
        username_disabled = kwargs.pop('username_disabled', False)
        self.username_value = kwargs.pop('username_value', False)
        super(UserForm, self).__init__(*args, **kwargs)
        if username_disabled:
            # self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].required = False
            self.fields['username'].widget.attrs['disabled'] = True
            self.fields['username'].help_text = ''
            # self.fields['username'].help_text = 'Cannot be changed.'
            # self.fields['email'].required = True

    # def clean_email(self):
    #     if User.objects.exclude(username=self.username_value).\
    #             filter(email__iexact=self.cleaned_data['email']):
    #         raise forms.ValidationError(validators.DUPLICATE_EMAIL)
    #     return self.cleaned_data['email']


class UserPasswordForm(UserForm, UserCreationForm):
    pass

# class UserPasswordForm(UserForm, RegistrationFormUniqueEmail):

    # def __init__(self, *args, **kwargs):
    #     super(UserPasswordForm, self).__init__(*args, **kwargs)
    #     self.fields['email'].help_text = ''
    #     self.fields['email'].label = 'Email address'


class EmailForm(Form):
    email = EmailField(required=True)
