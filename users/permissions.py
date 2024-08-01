from rest_framework.permissions import BasePermission


class IsFileUploader(BasePermission):
    """
    Проверяет, является ли текущий пользователь владельцем файла.
    """

    def has_object_permission(self, request, view, obj):
        """
        Определяет, имеет ли пользователь доступ к данному объекту.
        """
        # Если метод запроса - GET или HEAD, разрешаем доступ для всех
        if request.method in ['GET', 'HEAD']:
            return True

        # Проверяем, является ли пользователь владельцем файла
        return obj.user == request.user
