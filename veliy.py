from flask import Flask, render_template, request, redirect, url_for,session,flash, send_from_directory,send_file
from werkzeug.utils import secure_filename
from flask_bcrypt import generate_password_hash, check_password_hash
import psycopg2
from psycopg2 import sql
import os
from datetime import datetime, timedelta
from flask_login import login_user, current_user
from flask_cors import CORS
from werkzeug.utils import secure_filename
from urllib.parse import quote
import urllib.parse
import subprocess
import asyncio
from flask_caching import Cache






#Инициализации
app = Flask(__name__, template_folder='C:/Users/User/Desktop/veliy/code', static_folder='C:/Users/User/Desktop/veliy/static')

config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}
app.config.from_mapping(config)
cache = Cache(app)



CORS(app)
app.secret_key = 'SFgJSDfHUISFGJK454593VfVBR7BsSR8473dBsDSdbjsrhhkhluFG474ERDFDsSFSdFDS'
UPLOAD_FOLDER = 'uploads'
app.permanent_session_lifetime = timedelta(days=25)
ALLOWED_EXTENSIONS = {'ppt', 'pptx', 'doc', 'docx', 'pdf', '.rtf', '.pptm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 102 * 1024 * 1024 #ОБЬЕМ ФАЙЛА 102МБ МАКС



# Создаем папку, если ее нет
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
#Инициализация доп функций
#Соединение с бд


def create_db():
    try:
        with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost", port="5432") as conn:
            with conn.cursor() as cur:
                firstdata = '''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(10) UNIQUE NOT NULL,
                        password VARCHAR(100) NOT NULL,  -- Increased length for hashed password
                        email VARCHAR(20) UNIQUE NOT NULL
                    );
                '''
                cur.execute(firstdata)
                conn.commit()
    except Exception as e:
        print(f"Error creating database: {e}")

create_db()
#Функция загрузки нужных файлов

def create_and_rocognise_file_db():
    try:
        with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost",
                              port="5432") as conn:
            with conn.cursor() as cur:
                second_data = '''
                    CREATE TABLE IF NOT EXISTS filenames (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(100) NOT NULL,
                        user_id INTEGER NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id)

                    );
                '''
                cur.execute(second_data)
                conn.commit()
    except Exception as e:
        print(f"Error creating database: {e}")


create_and_rocognise_file_db()

def get_user_files(user_id):
    try:
        with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost", port="5432") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT filename FROM filenames WHERE user_id = %s", (user_id,))
                user_files = cur.fetchall()
                print("User files:", user_files)  # Отладочный вывод
                return user_files
    except Exception as e:
        print(f"Error retrieving user files: {e}")
        return None


def get_username_from_database(user_id):
    # Подключение к базе данных и выполнение запроса для получения имени пользователя
    try:
        conn = psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost", port="5432")
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        username = cur.fetchone()[0]  # Получаем имя пользователя из запроса
        conn.close()
        return username
    except Exception as e:
        print(f"Error getting username from database: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#Получение id из бд нужное для уникализации аккаунтов

def get_user_info_by_id(user_id):
    try:
        with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost", port="5432") as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM users WHERE id = %s"
                cur.execute(query, (user_id,))
                user = cur.fetchone()

                if user:
                    user_info = {
                        'id': user[0],
                        'name': user[1],
                        'email': user[3]
                        
                    }
                    return user_info
                else:
                    return None
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None
######

def get_user_id_by_email(email):
    try:
        with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost",
                              port="5432") as conn:
            with conn.cursor() as cur:
                query = "SELECT id FROM users WHERE email = %s"
                cur.execute(query, (email,))
                user_id = cur.fetchone()

                if user_id:
                    return user_id[0]
                else:
                    return None
    except Exception as e:
        print(f"Error getting user id by email: {e}")
        return None
#функция проверки на уникальность

def check(email, password):
    try:
        with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost", port="5432") as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM users WHERE email = %s"
                cur.execute(query, (email,))
                user = cur.fetchone()

                if user and check_password_hash(user[2], password):  # Check hashed password
                    session['user_id'] = user[0]
                    print("Авторизация успешна!")
                    return True
                else:
                    print("Авторизация не удалась. Неверный email или пароль.")

    except Exception as e:
        print(f"Error checking credentials: {e}")

    return False

#Функции страниц

#Главная
@app.route('/', methods=['POST', 'GET'])
@cache.cached(timeout=50)
def main():
    return render_template('home.html')
#О нас 
@app.route('/support')
@cache.cached(timeout=50)
def support():

    return render_template('VeliyAbout.html')

#Авториза и регистрация
@app.route('/login', methods=['POST', 'GET'])
def login():
    # проверка на сессию
    if 'user_id' in session:
        return redirect(url_for('personalpage', user_id=session.get('user_id')))

    user_id = None

    # регистрация
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if not username or not password or not email:
            flash('Пожалуйста, заполните все поля.', 'error')
        else:
            password_hash = generate_password_hash(password).decode('utf-8')  # Хеширование пароля

            try:
                with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost",
                                      port="5432") as conn:
                    with conn.cursor() as cur:
                        insert_users = sql.SQL(
                            "INSERT INTO users (name, password, email) VALUES (%s, %s, %s) RETURNING id ;")
                        cur.execute(insert_users, (username, password_hash, email))
                        user_id = cur.fetchone()[0]
                        conn.commit()
                        if user_id:
                            session['user_id'] = user_id
                            return redirect(url_for('personalpage', user_id=user_id))
                        else:
                            flash('Ошибка при регистрации. Попробуйте снова.', 'error')
            except Exception as e:
                print(f"Error inserting user data: {e}")
                flash('Ошибка при регистрации. Попробуйте снова.', 'error')

    # авторизация
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Пожалуйста, введите email и пароль.', 'error')
        else:
            if check(email, password):
                return redirect(url_for('personalpage', user_id=session.get('user_id')))
            else:
                flash('Авторизация не удалась. Неверный email или пароль.', 'error')

    return render_template('register.html')
    # авторизация





@app.route('/personalpage',methods=['POST', 'GET'])
def personalpage():
    if 'user_id' in session:
        user_id = session['user_id']
        user_info = get_user_info_by_id(user_id)
        username = get_username_from_database(user_id)
        if user_info:
            # Получаем имена файлов текущего пользователя
            filenames = get_user_files(user_id)
            if filenames is not None:  # Проверяем, что файлы успешно получены
                return render_template('grge.html', filenames=filenames, user_info=user_info, user_id=user_id,username=username)
            else:
                return "Ошибка при получении файлов пользователя."
        else:
            return "Ошибка: Пользователь не найден", 404
    else:
        return redirect(url_for('login'))

#тренды
@app.route('/trends')
@cache.cached(timeout=50)
def trends():
    return render_template('dev.html')
#каталог
@app.route('/catalog', methods=['POST', 'GET'])
@cache.cached(timeout=50)
def presentations():
    presentation_filenames = [filename for filename in os.listdir(app.config['UPLOAD_FOLDER']) if filename.endswith(('.ppt', '.pptx'))]
    word_doc_filenames = [filename for filename in os.listdir(app.config['UPLOAD_FOLDER']) if filename.endswith(('.doc', '.docx'))]
    pdf_filenames = [filename for filename in os.listdir(app.config['UPLOAD_FOLDER']) if filename.endswith('.pdf')]

    return render_template('pr1.html', presentation_filenames=presentation_filenames, word_doc_filenames=word_doc_filenames, pdf_filenames=pdf_filenames )
#скачать
@app.route('/upload/<filename>')
def download_file(filename):
     try:
        if allowed_file(filename):
            encoded_filename = quote(filename)
            return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(filename), as_attachment=True)
        else:
            return "Недопустимый тип файла", 400
     except FileNotFoundError:
         return "Файл не найден", 404
#выгрузка
@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Проверяем, есть ли файлы для загрузки
        if 'wordFile' not in request.files and 'presentationFile' not in request.files and 'pdfFile' not in request.files:
            return "Ошибка: Отсутствуют файлы для загрузки."

        # Получаем идентификатор пользователя
        user_id = session.get('user_id')

        # Получаем файлы из запроса
        word_file = request.files.get('wordFile')
        presentation_file = request.files.get('presentationFile')
        pdf_file = request.files.get('pdfFile')

        # Сохраняем файлы и получаем их имена
        filenames = []
        if word_file:
            word_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(word_file.filename))
            word_file.save(word_filename)
            filenames.append(word_filename)
        if presentation_file:
            presentation_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(presentation_file.filename))
            presentation_file.save(presentation_filename)
            filenames.append(presentation_filename)
        if pdf_file:
            pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf_file.filename))
            pdf_file.save(pdf_filename)
            filenames.append(pdf_filename)

        # Вставляем имена файлов в базу данных вместе с идентификатором пользователя
        with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost",
                              port="5432") as conn:
            with conn.cursor() as cur:
                for filename in filenames:
                    cur.execute("INSERT INTO filenames (filename, filename_only, user_id) VALUES (%s, %s, %s);", (filename, os.path.basename(filename), user_id))
                conn.commit()

        return "Файлы успешно загружены."
    except Exception as e:
        print(f"Error uploading files: {e}")
        return "Ошибка при загрузке файлов."

#поиск
@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search']
        all_files = []

        presentation_filenames = []
        word_doc_filenames = []
        pdf_filenames = []

        try:
            with psycopg2.connect(dbname="Usermans", user="postgres", password="moyasemya56", host="localhost",
                                  port="5432") as conn:
                with conn.cursor() as cur:
                    # Выполнение поискового запроса в базе данных для файлов с подходящими именами
                    query = "SELECT filename_only FROM filenames WHERE filename_only LIKE %s;"
                    cur.execute(query, ('%' + search_query + '%',))
                    search_results = [row[0] for row in cur.fetchall()]

                    # Фильтрация результатов поиска по типу файла
                    presentation_filenames = [filename for filename in search_results if
                                              filename.endswith(('.ppt', '.pptx'))]
                    word_doc_filenames = [filename for filename in search_results if
                                          filename.endswith(('.doc', '.docx'))]
                    pdf_filenames = [filename for filename in search_results if filename.endswith('.pdf')]

        except Exception as e:
            print(f"Error executing search query: {e}")
            # Если произошла ошибка, установите пустой список результатов поиска
            presentation_filenames = []
            word_doc_filenames = []
            pdf_filenames = []

    return render_template('pr1.html', presentation_filenames=presentation_filenames,
                           word_doc_filenames=word_doc_filenames, pdf_filenames=pdf_filenames, all_files=all_files)


@app.route('/help')
@cache.cached(timeout=50)
def help():
    return render_template('money.html')


@app.route('/adminpage',methods=['POST', 'GET'] )
def admin():
    # admin_email = "miralibaltbaeb59@gmail.com" admin_password = "moyasemya56@" if request.form['email] == admin_email and request.fort['password'] == admin_password: ку
    pass
#404
@app.errorhandler(404)
def page_not_found(e):
    
    return render_template('ERROR.html'), 404


if __name__ == '__main__':
    app.run(debug=True, port=7060,threaded=True )
