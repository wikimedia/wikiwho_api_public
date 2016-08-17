"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'wikiwho_api.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    title = _('WikiWho Dashboard')
    # template = 'grappelli/dashboard/dashboard.html'
    # template = 'admin/custom_dashboard.html'
    # columns = 2
    # children = None
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        request = context.get('request')
        # print(context)  # contains permissions and more - check the print
        # print(request)
        # print(context.get('perms'))
        # print(context.get('title'))
        context['title'] = '{} - {}'.format(self.title, request.user.get_full_name() or request.user.username)

        # append a group for "Administration" & "Applications"
        self.children.append(modules.Group(
            _('Group: Administration & Applications'),
            column=1,
            collapsible=True,
            children=[
                modules.AppList(
                    _('Administration'),
                    column=1,
                    collapsible=True,
                    models=('django.contrib.*',),
                ),
                modules.AppList(
                    _('Applications'),
                    column=1,
                    css_classes=('collapse closed',),
                    exclude=('django.contrib.*',),
                )
            ]
        ))
        
        # # append an app list module for "Applications"
        # self.children.append(modules.AppList(
        #     _('AppList: Applications'),
        #     collapsible=True,
        #     column=1,
        #     css_classes=('collapse closed',),
        #     exclude=('django.contrib.*',),  # Apps are displayed according to permissions!
        # ))
        #
        # # append an app list module for "Administration"
        # self.children.append(modules.ModelList(
        #     _('ModelList: Administration'),
        #     column=1,
        #     collapsible=False,
        #     models=('django.contrib.*',),
        # ))

        # append another link list module for "tools".
        self.children.append(modules.LinkList(
            _('Tools'),
            column=2,
            children=[
                {
                    'title': _('Clear cache'),
                    'url': '{}'.format(reverse('clear_cache')),
                    'external': False,
                },
                {
                    'title': _('Clear expired sessions'),
                    'url': '{}'.format(reverse('clear_sessions')),
                    'external': False,
                },
            ]
        ))
        
        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=True,
            column=2,
        ))

        # append a feed module
        self.children.append(modules.Feed(
            _('Latest Django News'),
            limit=5,
            feed_url='http://www.djangoproject.com/rss/weblog/',
            column=3
        ))
