from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import EmailDevice, SMSDevice

User = get_user_model()

class CustomUserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm

    # Define the fieldsets for the user admin panel
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email',
                        'inv_code', 'birthday', 'image', 'phone_number',
                        'username_change_count')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    # Define the fieldsets for the add user form
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
