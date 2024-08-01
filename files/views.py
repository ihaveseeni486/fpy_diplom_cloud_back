import logging
import os
import shutil
import uuid

from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomFile
from .permissions import IsAdminOrOwner
from .serializers import CustomFileSerializer
from users.models import CustomUser
from datetime import datetime
import mimetypes
from rest_framework.decorators import permission_classes
from users.serializers import UsersListSerializer
logger = logging.getLogger("files")


class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def generate_file_link(self):
        # Генерируем специальную ссылку на файл
        return f'{str(uuid.uuid4())}'

    def post(self, request, *args, **kwargs):
        logger.info("Запрос на загрузку файла на диск от пользователя %s", request.user)

        if not request.user.is_authenticated:
            logger.warning("Пользователь не авторизован %s", request.user)
            return Response({'message': 'не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)

        user_id = request.data.get('userId')
        logger.info("Попытка загрузки файла на диск пользователя с userId %s", user_id)
        # Проверяем, загружает ли файл администратор от имени другого пользователя
        if request.user.is_admin:
            if not user_id:
                logger.error("аАдмин upload without userId")
                return Response({'message': 'Необходим userId для загрузок администратором'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            # Если не администратор, убеждаемся, что пользователь загружает файл для себя
            if request.user.id != int(user_id):
                logger.warning(f"запрещенная попытка загрузки пользователем {request.user.id}")
                return Response({'message': 'запрещено'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден")
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Получаем данные из запроса
        file_obj = request.FILES['file']
        file_name = file_obj.name
        user_storage_path = user.user_storage_path
        logger.debug(f"User storage path: {user_storage_path}")
        file_path = os.path.join(user_storage_path, file_name)
        logger.debug(f"File path: {file_path}")
        special_link = self.generate_file_link()
        upload_date = datetime.now(),

        # смотрим есть ли у пользователя  файл с таким имененем:
        file = CustomFile.objects.filter(file_name=file_name, user_id=request.user.id)
        comment = request.data.get('comment')

        if file.exists():
            # Получаем текущее время
            current_time = datetime.now()
            # Форматируем текущее время в строку
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
            file_name = current_time_str + "_" + file_obj.name
            logger.info(f"File с таким именем существует. Имя файла изменено на {file_name}")

        file_new_path = os.path.join(user_storage_path, file_name)

        try:
            # Попытка сохранения файла
            custom_file = CustomFile(
                                     file_name=file_name,
                                     file_size=file_obj.size,
                                     user=user,
                                     comment=comment,
                                     #upload_date = upload_date,
                                     file_path=file_new_path,
                                     special_link=special_link,
            )
            custom_file.save()
            logger.info(f"File сохранен на сервере: {file_name}")
            # проверить что создан без ошибки и потом
            with open(file_new_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
                logger.info(f"File записан на диск по пути: {file_new_path}")
        except Exception as e:
            logger.error(f"File загружен с ошибкой: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = CustomFileSerializer(custom_file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# посчитать объем диска пользователя
def get_directory_size(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        logger.debug(f"Общий размер directory {path}: {total_size} bytes")
        return total_size


# посчитать количество файлов на диске пользователя
def count_user_files(user_storage_path):
        if os.path.exists(user_storage_path):
            file_count = len([f for f in os.listdir(user_storage_path) if os.path.isfile(os.path.join(user_storage_path, f))])
            logger.debug(f"Total file count in {user_storage_path}: {file_count}")
            return file_count
        return 0


User = get_user_model()


class ListFilesView(APIView):
    permission_classes = [permissions.IsAuthenticated,]

    def get(self, request):
        try:
            user_id = request.user.id
            # Получаем все объекты пользователей из базы данных
            files = CustomFile.objects.filter(user_id=user_id)

            # Сериализуем файлы в JSON
            serializer = CustomFileSerializer(files, many=True)

            # смотрим если пользователь администатор, высылаем список пользователей
            user = CustomUser.objects.get(id=user_id)

            if (user.is_admin):
                # Формируем список пользователей, исключая текущего
                users = CustomUser.objects.exclude(id=user_id)
                # Сериализуем пользователей в JSON
                serializer_users = UsersListSerializer(users, many=True)#UsersSerializer(users, many=True)

                # Рассчитываем занимаемое место для каждого пользователя
                users_data = serializer_users.data

                for user_data in users_data:
                    user_instance = CustomUser.objects.get(id=user_data['id'])
                    user_storage_path = user_instance.user_storage_path
                    user_data['storage_usage'] = get_directory_size(user_storage_path)
                    user_data['storage_count'] = count_user_files(user_storage_path)
                logger.debug(f"Admin user {user.username} запрашивает список всех пользователей")
                return Response({'files': serializer.data, 'users': users_data, 'status': 200 },
                                status=status.HTTP_200_OK)
            return Response({'files': serializer.data,}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in ListFilesView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# список файлов по id пользователя
class UserFilesView(APIView):
    permission_classes = [IsAdminOrOwner]

    def get(self, request, user_id):
        try:
            # Получаем все объекты пользователей из базы данных
            files = CustomFile.objects.filter(user_id=user_id)
            user = CustomUser.objects.get(id=user_id)
            # Сериализуем файлы в JSON
            serializer = CustomFileSerializer(files, many=True)
            logger.debug(f"User {request.user.id} запрашивает files для user {user_id}")
            return Response({'files': serializer.data,
                             'username': user.username, 'status': 200}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in UserFilesView: {e}")
            return Response({'error': str(e), 'status': 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'Запрещено', 'status': 403 }, status=status.HTTP_403_FORBIDDEN)


class FileDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id):
        logger.debug(f"Delete request for file ID {file_id}")
        try:
            file = CustomFile.objects.get(id=file_id)
            file_path = file.file_path
            # Проверяем, является ли пользователь владельцем файла или администратором
            if file.user == request.user or request.user.is_admin:
                file.delete()

                # Удаляем файл из файловой системы
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Файл {file_path} удален")
                    except OSError as e:
                        logger.error(f"Ошибка при удалении файла {file_path}: {e}")

                logger.info(f"File ID {file_id} удален пользователем {request.user.id}")
                return Response({"message": "File deleted successfully", 'status': 204},
                                status=status.HTTP_204_NO_CONTENT)
            else:
                logger.warning(f"Неавторизованная попытка удаления пользователем {request.user.id} for file ID {file_id}")
                return Response({"error": "You do not have permission to delete this file", 'status': 403},
                                status=status.HTTP_403_FORBIDDEN)
        except CustomFile.DoesNotExist:
            logger.error(f"File ID {file_id} not found")
            return Response({'error': 'File not found', 'status': 404}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in FileDeleteView: {e}")
            return Response({'error': str(e), 'status': 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadFileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(CustomFile, id=file_id)
        logger.debug(f"Запрос скачивания файла {file_id}")
        # Проверяем, является ли пользователь владельцем файла или администратором
        if file.user == request.user or request.user.is_admin:
            file_path = file.file_path
            try:
                print(f"Trying to open file: {file_path}")
                response = FileResponse(open(file_path, 'rb'),
                                        headers={'Content-Disposition': f'attachment; filename="{file.file_name}"',
                                                 'Content-Type': 'application/octet-stream',
                                                 'Access-Control-Expose-Headers': 'Content-Disposition'}, status=200)
                # устанавливаем дату скачивания
                file.last_download_date = datetime.now()
                file.save()
                logger.info(f"File Id {file_id} скачан пользователем ")
                return response
            except FileNotFoundError:
                logger.error(f"File Id {file_id} not found")
                return Response({"error": "File is not found", 'status': 404 },
                            status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error in DownloadFileView: {e}")
                return Response({"error": "An error occurred while trying to open the file", 'status': 500},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Неавторизованная попытка скачать файл {file_id} пользователем {request.user.id} ")
            return Response({"error": "You do not have permission to download this file"},
                            status=status.HTTP_403_FORBIDDEN)


@permission_classes([permissions.IsAuthenticated])
# изменение комментария
class ChangeCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        file_id = request.data.get('id')
        logger.debug(f"Change comment request for file ID {file_id}")
        file = get_object_or_404(CustomFile, id=file_id)
        # Проверяем, является ли пользователь владельцем файла или администратором
        if file.user == request.user or request.user.is_admin:
            try:
                serializer = CustomFileSerializer(file, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    logger.info(f"Comment изменен для file ID {file_id} пользователем {request.user.id}")
                return Response({"message": "Comment changed successfully"}, status=status.HTTP_204_NO_CONTENT)

            except Exception as e:
                logger.error(f"Error in ChangeCommentView: {e}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Неавторизованная попытка изменения комментария пользователем {request.user.id} в файле {file_id}")
            return Response({"error": "You do not have permission to delete this file"},
                                status=status.HTTP_403_FORBIDDEN)


# изменение названия файла
class ChangeNameView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        file_id = request.data.get('id')
        logger.debug(f"Запрос изменения названия для file id {file_id}")
        file = get_object_or_404(CustomFile, id=file_id)
        # Проверяем, является ли пользователь владельцем файла или администратором
        if file.user == request.user or request.user.is_admin:
            try:
                serializer = CustomFileSerializer(file, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()

                    # Получаем новое имя файла
                    new_file_name = serializer.validated_data.get('file_name', file.file_name)

                    # Получаем текущий путь к файлу в файловой системе
                    current_file_path = file.file_path

                    # Переименовываем или перемещаем файл в файловой системе
                    new_file_path = os.path.join(os.path.dirname(current_file_path), new_file_name)
                    shutil.move(current_file_path, new_file_path)

                    # Обновляем путь к файлу в модели
                    file.file_path = new_file_path
                    file.save(update_fields=['file_path'])

                    logger.info(f"Имя файла успешно изменено file ID {file_id} пользователем {request.user.id}")
                    logger.info(f"путь к файлу file ID {file_id}:  {new_file_path}")
                return Response({"message": "fileName changed successfully",
                                 'status': 204 }, status=status.HTTP_204_NO_CONTENT)

            except Exception as e:
                logger.error(f"Error in ChangeNameView: {e}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Неавторизованная попытка пользователем {request.user.id} изменения имени файла {file_id}")
            return Response({"error": "You do not have permission to change this file",
                             'status': 403 },
                            status=status.HTTP_403_FORBIDDEN)


class ShareLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(CustomFile, id=file_id)
        logger.debug(f"Запрос ссылки для файла {file_id}")
        # Проверяем, является ли пользователь владельцем файла или администратором
        if file.user == request.user or request.user.is_admin:
            try:
                link = file.special_link
                logger.info(f"Link shared для файла file ID {file_id} запрошенная пользователем {request.user.id}")
                return Response({"message": "fileName changed successfully", "link": link}, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Error in ShareLinkView: {e}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Неавторизованная попытка пользователем {request.user.id} для файла {file_id}")
            return Response({"error": "You do not have permission to delete this file"},
                            status=status.HTTP_403_FORBIDDEN)


class SpecialLinkView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, special_link):
        server = os.getenv('DB_HOST')
        logger.debug(f"Special link access request: {special_link}")
        try:
            custom_file = CustomFile.objects.get(special_link=special_link)
            file_path = custom_file.file_path
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type=mime_type)
                response['Content-Disposition'] = f'inline; filename={custom_file.file_name}'
                logger.info(f"Доступ к файлу special link: {special_link}")
                return response
        except CustomFile.DoesNotExist:
            logger.error(f"File with special link {special_link} not found")
            raise Http404("File not found")
