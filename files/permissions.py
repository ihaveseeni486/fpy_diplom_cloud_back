from rest_framework.permissions import BasePermission


class IsAdminOrOwner(BasePermission):
    def has_permission(self, request, view):
        # Разрешение предоставляется, если пользователь аутентифицирован
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешение предоставляется, если пользователь - администратор или владелец объекта
        return request.user.is_admin or obj.user_id == request.user.id