### Месенджер

<p>Это проект, в котором реализован мессенджер, для того, чтобы проект работал, необходимо, также установить backend часть <a href="https://github.com/BariBurik/Messenger_Fullstack_Frontend">Messenger_Fullstack_Frontend</a></p>

<p>Для запуска приложения, необходимо выполнить следующие команды, а также предварительно должен быть скачан PostgreSQL: 

```
# 1. Зайдите в psql от имени суперпользователя (по умолчанию это postgres)
sudo -u postgres psql # Для Linux
psql -U postgres -d postgres # Для Windows

-- 2. Создайте пользователя messenger_user с паролем 'postgres'
CREATE USER messenger_user WITH PASSWORD 'postgres';

-- 3. Создайте базу данных messenger с пользователем-владельцем messenger_user
CREATE DATABASE messenger OWNER messenger_user;

-- 4. (Опционально) Выход из psql
\q
```

```
# Активация виртуального окружения
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# Установка зависимостей
pip install -r requirements.txt

# Выполнение миграций
 python manage.py migrate

# Запуск сервера
python manage.py runserver
```
