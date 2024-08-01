import json
import logging
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

logger = logging.getLogger("api")


def get_csrf(request):
    response = JsonResponse({'detail': 'CSRF cookie set'})
    logger.info('CSRF cookie set для пользователя: %s', request.user)
    token = get_token(request)
    response['X-CSRFToken'] = token
    return response


@require_POST
def login_view(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    logger.info('Попытка входа: %')
    if username is None or password is None:
        logger.warning('Не удалось аутентифицировать пользователя: %s', username)
        return JsonResponse({'message': 'Please provide username and password.', 'status': 400}, status=400)
    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({'message': 'User is not found or login/password is incorrect.', 'status': 400}, status=400)
    login(request, user)
    logger.info('Вход в систему пользователя: %s', user.username)
    is_admin = user.is_admin
    return JsonResponse({'message': 'Successfully logged in.',
                         'username': username, 'userId': user.id,
                         'is_admin': is_admin, 'status': 200}, status=200)


def logout_view(request):
    user = request.user
    logger.info('Попытка выхода пользователя: %s', request.user.username)
    if not request.user.is_authenticated:
        logger.warning('Пользователь попытался выйти без аутентификации')
        return JsonResponse({'message': 'You\'re not logged in.'}, status=400)

    logout(request)
    logger.info('Пользователь вышел: %s', user)
    return JsonResponse({'message': 'Successfully logged out.'}, status=200)


@ensure_csrf_cookie
def session_view(request):
    if not request.user.is_authenticated:
        logger.warning('Неавторизованный доступ к просмотру сессии')
        return JsonResponse({'message': 'Your are not authenticated.', 'isAuthenticated': False}, status=403)

    user = request.user
    logger.info("Просмотр сессии аутентифицированным пользователем: %s", request.user.username)
    return JsonResponse({'message': 'Your are already authenticated.', 'isAuthenticated': True,
                         'userId': user.id, 'username': request.user.username,
                         'is_admin': user.is_admin, 'status': 200}, status=200)
