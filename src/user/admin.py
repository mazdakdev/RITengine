from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, path
from django.utils.html import format_html
from .otp_devices import EmailDevice, SMSDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from .utils.auth import remove_existing_2fa_devices

User = get_user_model()

class CustomUserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm

    readonly_fields = ('reset_2fa_button', 'preferred_2fa')

    # fieldsets for the user admin panel
    fieldsets = (
        (None, {'fields': ('username', 'password', 'preferred_2fa', 'reset_2fa_button')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email',
                        'inv_code', 'birthday', 'image', 'phone_number',
                        'username_change_count')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    # fieldsets for the add user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'email',
                'first_name', 'last_name', 'inv_code', 'birthday',
                'image', 'phone_number', 'is_staff', 'is_superuser'),
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_email_verified')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'inv_code')
    ordering = ('username',)

    def reset_2fa_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Reset 2FA</a>',
            reverse('admin:reset_2fa', args=[obj.pk])
        )

    reset_2fa_button.short_description = 'Reset 2FA'
    reset_2fa_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/reset-2fa/', self.admin_site.admin_view(self.reset_2fa), name='reset_2fa'),
        ]
        return custom_urls + urls

    @transaction.atomic
    def reset_2fa(self, request, user_id):
        user = self.get_object(request, user_id)
        try:
            remove_existing_2fa_devices(user)
            user.preferred_2fa = None
            user.save()

            self.message_user(request, f"2FA for {user.email} has been reset.")
        except Exception as e:
            self.message_user(request, f"An error occurred: {str(e)}", level='error')

        return HttpResponseRedirect(reverse('admin:user_customuser_change', args=[user_id]))


    def save_model(self, request, obj, form, change):
        """
        Override the save_model method to ensure
        is_email_verified is set to True by default.
        """
        if not change:
            obj.is_email_verified = True
        super().save_model(request, obj, form, change)


admin.site.register(User, CustomUserAdmin)
admin.site.register(SMSDevice)
