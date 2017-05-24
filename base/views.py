import os

from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


@staff_member_required
def clear_cache(request):
    call_command('clear_cache')
    messages.add_message(request, messages.SUCCESS, 'Cache is cleared!')
    return HttpResponseRedirect(reverse('admin:index'))


@staff_member_required
def clear_sessions(request):
    call_command('clearsessions')
    messages.add_message(request, messages.SUCCESS, 'Expired sessions are deleted from database!')
    return HttpResponseRedirect(reverse('admin:index'))


def download(request, file_name):
    download_path = '/home/nuser/dumps/wikiwho_dataset/outputs/download'
    file_path = os.path.join(download_path, file_name)
    if os.path.dirname(file_path) == download_path and os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type='application/force-download')
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    raise Http404('{} is not available to download'.format(file_name))
