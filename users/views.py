import os
import shutil

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.middleware.csrf import get_token
from rest_framework import status, viewsets, generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from files.models import CustomFile
from .models import CustomUser
from .serializers import UsersSerializer, UserUpdateSerializer, UsersListSerializer
from django.contrib.auth import get_user_model
import logging
logger = logging.getLogger("users")
from rest_framework.decorators import permission_classes


def check_pass(provided_password, hashed_password):
    logger.debug("проверка пароля")
    if check_password(provided_password, hashed_password):
        return True
    else:
        return False


@permission_classes([permissions.IsAuthenticated])
# Изменение пользователя
class ChangeUser(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserUpdateSerializer

    def get_object(self):
        # Получение пользователя на основе переданного в URL user_id или текущего пользователя
        user_id = self.kwargs.get('userId')

        if user_id:
            return CustomUser.objects.get(id=user_id)
        return self.request.user

    def patch(self, request, *args, **kwargs):
        logger.debug(f"Запрос {request.user} на изменение пользователя")
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if not (request.user.is_admin or request.user == instance):
            logger.warning(f"Пользователь {request.user} пытался изменить данные пользователя {instance.username}")
            return Response({'error': 'У вас нет прав для изменения этих данных.'}, status=status.HTTP_403_FORBIDDEN)

        old_username = instance.username  # Сохраняем старое имя пользователя

        # если изменился у пользака логин, то нужно проверить его уникальность
        if old_username != request.data['username'] and User.objects.filter(username=request.data['username']).exists():
            logger.warning(f"Пользователь с таким именем уже существует")
            return Response({'message': 'Пользователь с таким именем уже существует.', 'status': 400},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        new_username = serializer.validated_data.get('username', old_username)

        # Если имя пользователя изменилось, обновляем директорию хранения файлов
        if new_username != old_username:

            old_storage_path = instance.user_storage_path
            new_storage_path = os.path.join(settings.STORAGE_DIR, new_username)
            instance.user_storage_path = new_storage_path

            # Перемещение файлов в новую директорию
            if os.path.exists(old_storage_path):
                shutil.move(old_storage_path, new_storage_path)
                # Удаление старой пустой директории
                try:
                    os.rmdir(old_storage_path)
                except OSError as e:
                    logger.warning(f"Не удалось удалить директорию {old_storage_path}: {e}")
            else:
                os.makedirs(new_storage_path, exist_ok=True)

            instance.save(update_fields=['user_storage_path'])

            # Обновление file_path для всех файлов пользователя
            user_files = CustomFile.objects.filter(user=instance)
            for file in user_files:
                old_file_path = file.file_path
                new_file_path = os.path.join(new_storage_path, file.file_name)
                print(new_file_path,'new_file_path')
                file.file_path = new_file_path
                file.save(update_fields=['file_path'])
                logger.info(f"Обновлен путь файла {file.file_name} на {new_file_path}")

        logger.info(f"пользователь {instance.username} был обновлен")
        return Response(serializer.data, status=status.HTTP_200_OK)


# Регистрация пользователя
class RegisterUser(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # Генерация CSRF-токена
        csrf_token = get_token(request)
        serializer = UsersSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Аутентификация пользователя
            user = authenticate(username=serializer.validated_data['username'],
                                password=serializer.validated_data['password'])
            if user is not None:
                login(request, user)
                logger.info(f"Новый пользователь {user.username} зарегистрирован и аутентифтцтрован")
            #authenticate(username=serializer.data['username'], password=serializer.data['password'])
            return Response({'message': 'User is created successfully.',
                             'csrf_token': csrf_token,
                             'username': serializer.data['username'],
                             'id': serializer.data['id'],
                             }, status=status.HTTP_201_CREATED)
        logger.error(f'Ошибка при регистрации пользователя: {serializer.errors}')
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# Удаление пользователя
class DeleteUser(APIView):

    def delete(self, request, userId):
        logger.debug(f'Запрос на удаление пользователя userId={userId}')
        if request.user.is_authenticated and request.user.is_admin:
            try:
                # Получаем имя пользователя из параметров запроса
                userId = userId
                if not userId:
                    return Response({"error": "userId parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
                # Получаем пользователя по его имени
                user = CustomUser.objects.get(id=userId)
                user_storage_path = user.user_storage_path
                username = user.username
                # Удаляем пользователя
                user.delete()
                logger.info(f'Пользователь {username} (userId={userId}) удален')

                # Удаляем директорию пользователя
                if os.path.exists(user_storage_path):
                    try:
                        shutil.rmtree(user_storage_path)
                        logger.info(f'Директория {user_storage_path} для пользователя {username} удалена')
                    except OSError as e:
                        logger.error(
                            f'Ошибка при удалении директории {user_storage_path} для пользователя {username}: {e}')

                return Response({"message": f"User '{username}' con userId '{userId}' deleted successfully."}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                logger.error(f'Пользователь с userId={userId} не найден')
                return Response({"message": f"User con userId '{userId}' does not exist."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.exception(f'Ошибка при удалении пользователя userId={userId}: {str(e)}')
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f'Неавторизованный запрос на удаление пользователя userId={userId}')
            return Response({"message": "username is not authenticated"}, status=status.HTTP_403_FORBIDDEN)


# поменять статус пользователя is_admin
class ChangeStatusAdmin(APIView):

    def patch(self, request, userId):
        logger.debug(f'Запрос на изменение статуса администратора для userId={userId}')
        if request.user.is_admin:
            try:
                # Получаем конктретного пользователя из базы данных
                statusAdmin = request.data.get('statusAdmin')
                # Преобразуем строковое значение в булево
                if statusAdmin.lower() == 'true':
                    statusAdmin = True
                elif statusAdmin.lower() == 'false':
                    statusAdmin = False

                user = CustomUser.objects.get(id=userId)  # Используем get для получения одного объекта
                user.is_admin = statusAdmin
                user.save()  # Сохраняем изменения
                logger.info(f'Статус администратора для пользователя {user.username} (userId={userId}) изменен на {statusAdmin}')
                return Response( {'message': 'status is changed succesfully' }, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                logger.error(f'Пользователь с userId={userId} не найден')
                return Response({"message": f"User con userId '{userId}' does not exist."},
                            status=status.HTTP_404_NOT_FOUND)
        else:
            logger.warning(f'Неавторизованный запрос на изменение статуса администратора для userId={userId}')
            return Response({"message": "username is not authenticated"}, status=status.HTTP_403_FORBIDDEN)


def get_directory_size(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        logger.debug(f"подсчет размера используемого хранилища ")
        return total_size


# посчитать количество файлов на диске пользователя
def count_user_files(user_storage_path):
    if os.path.exists(user_storage_path):
        total_files = len([f for f in os.listdir(user_storage_path) if os.path.isfile(os.path.join(user_storage_path, f))])
        logger.debug(f"подсчет общего количества файлов ")
        return total_files
    return 0


User = get_user_model()


# получение списка пользовтаелей с их данными
class UsersList(APIView):
            permission_classes = [IsAuthenticated]

            def get(self, request):
                user_id = request.user.id
                # смотрим если пользователь администатор, высылаем список пользователей
                user = CustomUser.objects.get(id=user_id)
                if user.is_admin:
                    # Формируем список пользователей, исключая текущего
                    users = CustomUser.objects.exclude(id=user_id)
                    # Сериализуем пользователей в JSON
                    serializer_users = UsersListSerializer(users, many=True)  # UsersSerializer(users, many=True)

                    # Рассчитываем занимаемое место для каждого пользователя
                    users_data = serializer_users.data

                    for user_data in users_data:
                        user_instance = CustomUser.objects.get(id=user_data['id'])
                        user_storage_path = user_instance.user_storage_path
                        user_data['storage_usage'] = get_directory_size(user_storage_path)
                        user_data['storage_count'] = count_user_files(user_storage_path)
                        logger.debug(f'Пользователь {user_data["username"]} имеет {user_data["storage_count"]} '
                                     f'файлов и использует {user_data["storage_usage"]} байт')
                    logger.info('Администратор запросил список пользователей')
                    return Response({'users': users_data, 'status': 200},
                            status=status.HTTP_200_OK)
                else:
                    # если не администратор
                    serializer_user = UsersListSerializer([user], many=True)
                    logger.info(f'Пользователь {user.username} запросил свои данные')
                    return Response({'user': serializer_user.data, 'status': 200},
                                    status=status.HTTP_200_OK)


# получение данных профиля пользователя
class UserData(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):

        user = request.user
        if user_id != request.user.id and user.is_admin is not True:
            logger.warning(f'Пользователь {user.username} пытался получить данные другого пользователя')
            return Response({'error': 'Forbidden', 'status': 403},
                            status=status.HTTP_403_FORBIDDEN)

        userObject = CustomUser.objects.get(id=user_id)
        serializer_user = UsersListSerializer([userObject], many=True)
        logger.info(f'Пользователь {user.username} запросил данные пользователя user_id={user_id}')
        return Response({'user': serializer_user.data, 'status': 200},
                        status=status.HTTP_200_OK)
