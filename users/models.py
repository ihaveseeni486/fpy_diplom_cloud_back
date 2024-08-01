import os
import shutil

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.contrib.auth.hashers import make_password


class CustomUserManager(BaseUserManager):
    def create_user(self, username, full_name, email, password, is_admin=False, user_storage_path=None):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user_storage_path = os.path.join(settings.STORAGE_DIR, username)
        user = self.model(username=username, full_name=full_name, email=email, is_admin=is_admin, user_storage_path=user_storage_path)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, full_name, email, password=None):
        user = self.create_user(username, full_name, email, password, is_admin=True)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.
    """
    objects = CustomUserManager()
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    user_storage_path = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        LogEntry.objects.filter(user_id=self.id).delete()
        super(CustomUser, self).delete(*args, **kwargs)

    # При создании нового пользователя в БД создается его хранилище на сервере
    def save(self, *args, **kwargs):
        created = not self.pk  # Если запись создается впервые
        print(self.pk,'self.pk')
        super().save(*args, **kwargs)
        if created:
            self.user_storage_path = os.path.join(settings.STORAGE_DIR, self.username)
            os.makedirs(self.user_storage_path, exist_ok=True)
            super().save(update_fields=['user_storage_path'])

    # При удалении пользователя из БД удаляется его директория в хранилище
    def delete(self, *args, **kwargs):
        # Удаляем хранилище пользователя перед удалением самого пользователя
        user_storage_path = self.user_storage_path
        if os.path.exists(user_storage_path):
            shutil.rmtree(user_storage_path)

        # Вызываем стандартный метод удаления
        super().delete(*args, **kwargs)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name', 'email']

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)
