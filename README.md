# Облачное хранилище My Cloud

Изначальное [задание к дипломному проекту проекту](https://github.com/netology-code/fpy-diplom/blob/main/README.md).
Ссылка на гит, где [frontend](https://github.com/ihaveseeni486/fpy_diplom_cloud_front).
Ссылка на гит, где [backend](https://github.com/ihaveseeni486/fpy_diplom_cloud_back).

--------
Созданное хранилище предназначено хранения файлов пользователей и для управления ими. Пользователи могут регистрироваться, 
входить в систему и выходить из нее, доступны возможности загрузки/удаления/изменения файлов, генерация внешних ссылок на 
файлы для предоставления доступа к ним третьим лицам. Ограничение на размер загружаемых файлов на сервер регулируется настройками 
на сервере и указаны ниже в командах установки приложения.
Для пользователя с признаком администратор возможно смотреть список всех пользователей приложения и управлять файлами 
всех пользователей.
Приложение построено с использованием Django (backend) и React с Vite (frontend).

Для суперпользователя, созданного при deploy проекта, доступна административная панель Django приложения по адресу server/admin/

### Структура проекта на сервере:
```
/корневая-директория-сервера
├── /home
│  ├── /admin # Директория пользователя сервера, создается администратором
│  │  ├── /корневая-директория-проекта, созданная клонированием с GitHub
│  │  │  ├──/api # Файлы приложения API
│  │  │  ├──/app # Файлы основного приложения APP
│  │  │  ├──/files # Файлы приложения FILES
│  │  │  ├──/storage # Директория для хранения файлов пользователей. Создается администратором при разворачивании проекта.
│  │  │  │  ├──/user # директория пользователя, создается при регистрации пользователя а приложении
│  │  │  ├──/users # Файлы приложения USERS
│  │  │  ├──/static # Статические файлы (CSS, JavaScript, изображения)
│  │  │  │  ├── /react # Директория создается администратором.
│  │  │  │  │  ├── /dist # Копируем в /react папку, созданную в процессе сборки frontend React Vite приложения
│  │  │  │.env
│  │  │  │.gitignore
│  │  │  │info.log # Файл для записи логов
│  │  │  │manage.py # Скрипт управления Django
│  │  │  │README.md # Обзор проекта и документация
│  │  │  │requirements.txt # Зависимости Python
```

### Deploy приложения на сервере.

1. Настраиваем SSH ключ для безопасного подключения к серверу и для подтверждения своей идентичности.
Можно через git bash в терминале:
```angular2html
ssh-keygen
```
для копирования ssh ключа (ручками из терминала забираем в буфер без окончания с именем пользователя и 
машины):
```angular2html
cat ~/.ssh/id_rsa.pub
```
2. На сервисе [reg.ru](https://www.reg.ru/vps/) необходимо арендовать виртуальный сервер VPS с ОС Ubuntu (Мои ресурсы - Создать сервер - 
ОС Ubuntu, для данного проекта тариф самый дешевый) и заносим наш ssh ключ. 

Если его сразу при создании не занести, то можно внести в личном кабинете сервиса REG.RU (выбираем настройку SSL, 
где применяем ранее скопированный SSH ключ).
3. Используя терминал и логин/пароль, которые пришли на почту после аренды сервера,
заходим на сервер через терминал:
```
ssh root@ip_adress_server  
```
где root - это логин, а ip_adress_server - ip созданного сервера.
4. Создаем нового пользователя:
```
adduser admin 
 ```
где admin - это имя нового пользователя и подтверждаем паролем.
5. Предоставляем права новому пользователю: 
```
usermod admin -aG sudo
```
6. Переключаем на пользователя:
```
sudo su admin
```
7. Переходим в его директорию:
```angular2html
cd ~
```
8. Обновляем пакетный менеджер командой:
```
sudo apt update
```
9. Устанавливаем postgres, venv и pip:
```
sudo apt install python3-pip postgresql python3-venv
```
И проверяем, активный ли postgres:
```
sudo systemctl status postgresql 
```
Если нет, то дополнительно:
```
sudo systemctl start postgresql
```
10. Заходим под пользователем postgres в систему sql:
```
sudo su postgres
psql
```

11. Cоздаем пользователя БД:
```
CREATE USER admin;
```
12. Создаем для него пароль: 
```
ALTER USER admin WITH PASSWORD 'password';
```
13. Присваиваем права суперпользователя:
```
ALTER USER admin WITH SUPERUSER; 
```
14. Cоздаем БД с таким же именем как пользователь:
```
CREATE DATABASE admin;
```
15. Выходим из системы:
```
\q
Exit
```
и заходим под своим именем (это позволит преодолеть ошибку Permission denied):
```
admin@cv3998423:~$ psql
```
18. Создаем БД и снова выходим:
```
CREATE DATABASE cloud_project;
\q
```
____________________________________________________________
19. Клонируем проект с github:
```
git clone https://github.com/ihaveseeni486/fpy_diplom_cloud_back.git
```
20. Переходим в папку проекта:
```
cd fpy_diplom_cloud_back
```
21. Создаем виртуальные окружение:
```
python3 -m venv env
```
22. Активируем виртуальные окружение:
```
source env/bin/activate (на серверной)
source env/scripts/activate (у себя локально)
```
23. Устанавливаем все зависимости из проекта:
```
pip install -r requirements.txt
```
24. Создаем файл .env:
```
nano .env
```
25. Записываем в файле данные для работы приложения:
```
SECRET_KEY=8@!rm9a8r+7z=oqyqkz-0inj@3dskfhslf9&2ee^ez&69q9mr1dfku%s+t
DEBUG=False
ALLOWED_HOSTS=ip_address_сервера
DB_ENGINE=django.db.backends.postgresql
DB_NAME=cloud_project
DB_USER=admin
DB_PASSWORD=password_наш
DB_HOST=localhost
DB_PORT=5432
```
где SECRET_KEY - произвольный набор символов. Можно сгенерировать на [сервисе](https://djecrety.ir/).
26. В активированном виртуальном окружении применяем миграции из проекта: 
```
python manage.py migrate
```
27. Создаем суперпользователя admin:
```angular2html
python manage.py createsuperuser
```
28. Собираем статику (иначе у нас интерфейс у django не соберется): 
```
python manage.py collectstatic
```
29. Выходим из виртуального окружения и устанавливаем nginx и запускаем:
```
deactivate
sudo apt install nginx
sudo systemctl start nginx
```
30. Настраиваем конфигурационные файлы для управления nginx:
```angular2html
sudo nano /etc/nginx/sites-available/project
```
где вместо project может быть любое имя.
содержимое файла:
```angular2html
server {
    listen 80;
    server_name 194.58.126.189;

    location / {
        root /home/admin/fpy_diplom_cloud_back/static/react/dist/;
        try_files $uri $uri/ /index.html;
    }

    # Обслуживание статических файлов
    location /static/ {
        alias /home/admin/fpy_diplom_cloud_back/static/;
        try_files $uri $uri/ =404;
    }
    # Проксирование запросов к /admin/ на Django-сервер
    location /admin/ {
        proxy_pass http://unix:/home/admin/fpy_diplom_cloud_back/app/project.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
# Проксирование запросов к /api/ на Django-сервер
    location /api/ {
        proxy_pass http://unix:/home/admin/fpy_diplom_cloud_back/app/project.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    # Проксирование запросов к /storage/ на Django-сервер
    location /storage/ {
        proxy_pass http://unix:/home/admin/fpy_diplom_cloud_back/app/project.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
        # Проксирование запросов к /users/ на Django-сервер
    location /users/ {
        proxy_pass http://unix:/home/admin/fpy_diplom_cloud_back/app/project.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

```
31. Открываем редактор ```sudo nano /etc/nginx/nginx.conf``` и добавляем:
```
http {
...
    upstream backend {
        server unix:/home/admin/fpy_diplom_cloud_back/app/project.sock;
    }   
    
    client_max_body_size 10000M;  # увеличиваем ограничение на размер файлов, допустимого для пользователей.

...
```
32. Создаем ссылку:
```
sudo ln -s /etc/nginx/sites-available/project /etc/nginx/sites-enabled/
```
33. Устанавливаем wsgi сервер для взаимодействия веб-сервера и python приложением. Будем устанавливать 
библиотеку gunicorn. Активируем виртуальное окружение и устанавливаем 
```
source env/bin/activate
pip install gunicorn
```
34. Указываем как подключать gunicorn: 
```
gunicorn app.wsgi --bind 0.0.0.0:8000
 ```
где app - это основное python приложение, а порт это то, к чему привязываем gunicorn.

35. Настраиваем, чтобы gunicorn был всегда запущен. Выходим из виртуального окружения и открываем конфигурационный файл:
```
ctrl+c
sudo nano /etc/systemd/system/gunicorn.service
```
Содержимое файла:
```
[Unit]
Description=service for wsgi
After=network.target

[Service]
User=admin
Group=www-data
WorkingDirectory=/home/admin/fpy_diplom_cloud_back
ExecStart=/home/admin/fpy_diplom_cloud_back/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/admin/fpy_diplom_cloud_back/app/project.sock app.wsgi:application

[Install]
WantedBy=multi-user.target
```
36. Активируем gunicorn:
```angular2html
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```
37. Перезапускаем nginx:
```angular2html
sudo systemctl restart nginx
```
Если при запуске сервера будет ошибка 500 и в логах ```sudo tail -n 50 /var/log/nginx/error.log```
сообщение Permission denied необходимо предоставить 
доступ nginx к Permission:
Или также может быть ошибка 502 bad gateway, она решается также:
```/home/admin/fpy_diplom_cloud_back/static/react/dist/:```
```angular2html
sudo chmod 755 /home/admin
sudo chown -R admin:www-data /home/admin/fpy_diplom_cloud_back
sudo systemctl restart nginx
sudo systemctl restart gunicorn
```

-------------------------------------------
### deploy react приложения

 - Перейдите в редактор вашего React-проекта и выполните команду сборки:
```
npm run build
```
в результате сборки будем создана папка dist в корне проекта react.
- На сервере в директории fpy_diplom_cloud_back/static создаем директорию react и перемещаем туда созданную ранее папку dist.

