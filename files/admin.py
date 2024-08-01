from django.contrib import admin
from .models import CustomFile


class CustomFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'file_size', 'upload_date', 'comment')
    search_fields = ('file_name', 'user__username', 'comment')
    list_filter = ('upload_date', 'user')


admin.site.register(CustomFile, CustomFileAdmin)
