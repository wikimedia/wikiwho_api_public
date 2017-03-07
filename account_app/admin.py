from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Account


class AccountAdmin(admin.ModelAdmin):
    search_fields = ('company', )
    list_display = ('user', 'company', )
    # list_filter = ('company', )


class AccountInline(admin.StackedInline):
    model = Account
    can_delete = False
    verbose_name_plural = 'accounts'


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', )
    list_editable = ('is_active', )
    inlines = (AccountInline, )

admin.site.register(Account, AccountAdmin)
# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
