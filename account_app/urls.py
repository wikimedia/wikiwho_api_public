from django.conf.urls import url
from django.contrib.auth.views import login, logout, password_change, password_reset_done, password_reset_confirm

from .views import account_detail, register, RegistrationCompletedView, send_activation_email, ActivationView, \
    password_reset

urlpatterns = [
    url(r'^$', account_detail, name='detail'),
    url(r'^login/$', login, {'template_name': 'account_app/login.html'}, name='login'),
    url(r'^logout/$', logout, {'template_name': 'account_app/logout.html'}, name='logout'),
    url(r'^register/$', register, name='register'),
    url(r'^register/complete/$', RegistrationCompletedView.as_view(), name='registration_complete'),
    url(r'^activate/send_email/$', send_activation_email, name='send_activation_email'),
    # The activation key can make use of any character from the URL-safe base64 alphabet, plus the colon as a separator.
    url(r'^activate/(?P<activation_key>[-:\w]+)/$', ActivationView.as_view(), name='registration_activate'),
    url(r'^change_password/$', password_change, {'template_name': 'account_app/password_change_form.html',
                                                 'post_change_redirect': 'account:detail'},
        name='password_change'),
    url(r'^reset_password/$', password_reset, name='password_reset'),
    url(r'^reset_password_done/$', password_reset_done, {'template_name': 'account_app/password_reset_done.html'},
        name='password_reset_done'),
    url(r'^reset_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm, {'template_name': 'account_app/password_reset_confirm.html',
                                 'post_reset_redirect': 'account:login'},
        name='password_reset_confirm'),
]
