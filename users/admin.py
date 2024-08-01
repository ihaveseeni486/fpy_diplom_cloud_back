
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'full_name', 'email', 'is_admin',
                    'user_storage_path', 'view_files')  # Поля, которые будут отображаться в списке пользователей

    fieldsets = (
        (None, {'fields': ('username', 'full_name', 'email', 'password')}),
        # Определение полей в форме создания/редактирования пользователя
        ('Permissions', {'fields': ('is_admin', 'is_active', 'is_staff', 'groups', 'user_permissions')}),
    # Поля, связанные с разрешениями
    )

    def view_files(self, obj):
        url = reverse('admin:files_customfile_changelist') + f'?user__id__exact={obj.id}'
        return format_html('<a href="{}">Посмотреть файлы</a>', url)

    view_files.short_description = 'Файлы'


admin.site.register(CustomUser, CustomUserAdmin)
