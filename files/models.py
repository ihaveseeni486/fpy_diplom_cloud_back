import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from users.models import CustomUser


class CustomFile(models.Model):

    user = models.ForeignKey(CustomUser, related_name='files', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)  # Оригинальное имя файла
    file_size = models.BigIntegerField()  # Размер файла
    upload_date = models.DateTimeField(auto_now_add=True)  # Дата загрузки (автоматически устанавливается при создании)
    last_download_date = models.DateTimeField(null=True, blank=True)  # Последняя дата скачивания
    comment = models.TextField(max_length=255, blank=True)  # Комментарий
    file_path = models.CharField(max_length=255)  # Путь к файлу в хранилище
    special_link = models.CharField(max_length=255)  # Специальная ссылка для скачивания

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        print('сохранение в модели')
        user = kwargs.pop('user', None)
        super().save()

    class Meta:
        verbose_name = 'Файл'
        verbose_name_plural = "Список всех файлов"
        ordering = ('user',)
