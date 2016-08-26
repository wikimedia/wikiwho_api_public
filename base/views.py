from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


@staff_member_required
def clear_cache(request):
    cache.clear()
    messages.add_message(request, messages.SUCCESS, 'Cache is cleared!')
    return HttpResponseRedirect(reverse('admin:index'))


@staff_member_required
def clear_sessions(request):
    call_command('clearsessions')
    messages.add_message(request, messages.SUCCESS, 'Expired sessions are deleted from database!')
    return HttpResponseRedirect(reverse('admin:index'))
