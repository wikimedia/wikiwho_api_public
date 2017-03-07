from registration.views import RegistrationView
from registration.backends.hmac.views import RegistrationView, ActivationView as BaseActivationView

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.views import password_reset as base_password_reset

from account_app.models import Account
from api.utils import get_throttle_data

from .forms import UserForm, AccountForm, UserPasswordForm, EmailForm


@login_required
@csrf_protect
def account_detail(request):
    user = request.user
    account = user.account

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create 2 form instances and populate them with data from the request:
        user_form = UserForm(request.POST, prefix='user', username_disabled=True, username_value=user.username)
        account_form = AccountForm(request.POST, prefix='account')

        # check whether they are valid:
        if user_form.is_valid() and account_form.is_valid():
            # process the data in form.cleaned_data as required
            user_update_fields = []
            if user.email != user_form.cleaned_data['email']:
                user_update_fields.append('email')
                user.email = user_form.cleaned_data['email']
            if user.first_name != user_form.cleaned_data['first_name']:
                user_update_fields.append('first_name')
                user.first_name = user_form.cleaned_data['first_name']
            if user.last_name != user_form.cleaned_data['last_name']:
                user_update_fields.append('last_name')
                user.last_name = user_form.cleaned_data['last_name']
            if user_update_fields:
                user.save(update_fields=user_update_fields)

            account_update_fields = []
            if account.company != account_form.cleaned_data['company']:
                account_update_fields.append('company')
                account.company = account_form.cleaned_data['company']
            if account_update_fields:
                account.save(update_fields=account_update_fields)

            return HttpResponseRedirect(reverse('account:detail'))
    # if a GET (or any other method) we'll create blank forms
    else:
        user_form = UserForm(instance=user, prefix='user', username_disabled=True)
        account_form = AccountForm(instance=account, prefix='account')

    context = {'user_form': user_form,
               'account_form': account_form,
               'user': request.user,
               'throttle_data': get_throttle_data(request)}
    return render(request, 'account_app/detail.html', context)


def _send_activation_email(request, user):
    rv = RegistrationView()
    rv.request = request
    rv.email_body_template = 'account_app/activation_email.txt'
    rv.email_subject_template = 'account_app/activation_email_subject.txt'
    rv.send_activation_email(user)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def register(request):
    if request.user and request.user.is_authenticated:
        return render(request, 'account_app/register.html', {})
    if request.method == 'POST':
        user_form = UserPasswordForm(request.POST, prefix='user')
        account_form = AccountForm(request.POST, prefix='account')

        if user_form.is_valid() and account_form.is_valid():
            extra_fields = {'is_active': False,  # will set to True after activation
                            'first_name': user_form.cleaned_data['first_name'],
                            'last_name': user_form.cleaned_data['last_name']}
            user = User.objects.create_user(user_form.cleaned_data['username'],
                                            user_form.cleaned_data['email'],
                                            user_form.cleaned_data['password2'],
                                            **extra_fields)
            account = Account.objects.create(user=user, company=account_form.cleaned_data['company'])
            _send_activation_email(request, user)
            # from django.contrib import messages
            # messages.add_message(request, messages.INFO, 'Hello world.{}-{}'.format(user.email, settings.ACCOUNT_ACTIVATION_DAYS))
            # context = {'email': user.email,
            #            'activation_days': settings.ACCOUNT_ACTIVATION_DAYS}
            # return render(request, 'account_app/registration_complete.html', context)
            return HttpResponseRedirect(reverse('account:registration_complete'))
    else:
        user_form = UserPasswordForm(prefix='user')
        account_form = AccountForm(prefix='account')

    context = {'user_form': user_form,
               'account_form': account_form}
    return render(request, 'account_app/register.html', context)


class RegistrationCompletedView(TemplateView):
    template_name = 'account_app/registration_complete.html'

    def get_context_data(self, **kwargs):
        context = super(RegistrationCompletedView, self).get_context_data(**kwargs)
        context.update({'activation_days': settings.ACCOUNT_ACTIVATION_DAYS})
        return context


class ActivationView(BaseActivationView):
    template_name = 'account_app/activation_failed.html'

    def get_success_url(self, user):
        return 'account:detail', (), {}

    def activate(self, *args, **kwargs):
        user = super(ActivationView, self).activate(*args, **kwargs)
        if user:
            login(self.request, user=user)
        return user

    def get_context_data(self, **kwargs):
        context = super(ActivationView, self).get_context_data(**kwargs)
        context.update({'activation_days': settings.ACCOUNT_ACTIVATION_DAYS})
        # 'protocol': self.request.is_secure()
        # current_site = get_current_site(request)
        # site_name = current_site.name
        # domain = current_site.domain
        return context


@csrf_protect
@never_cache
def send_activation_email(request):
    if request.method == 'POST':
        email_form = EmailForm(request.POST)
        if email_form.is_valid():
            try:
                user = User.objects.get(email=email_form.cleaned_data['email'])
            except User.DoesNotExist:
                email_form.add_error('email', 'This email address is not registered.')
            else:
                _send_activation_email(request, user)
                return HttpResponseRedirect(reverse('account:registration_complete'))
    else:
        email_form = EmailForm()

    context = {'form': email_form}
    return render(request, 'account_app/activation_send_email.html', context)


def password_reset(request):
    return base_password_reset(request,
                               template_name='account_app/password_reset_form.html',
                               email_template_name='account_app/password_reset_email.txt',
                               # subject_template_name='registration/password_reset_subject.txt',
                               # password_reset_form=PasswordResetForm,
                               # token_generator=default_token_generator,
                               post_reset_redirect='account:password_reset_done',
                               from_email=None,  # TODO
                               extra_context=None,
                               html_email_template_name=None,
                               extra_email_context=None)
