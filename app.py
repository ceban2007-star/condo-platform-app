# -*- coding: utf-8 -*-
# app.py

import os 
# Добавляем login_required, current_user, LoginManager
from flask import Flask, render_template, request, redirect, url_for, flash 
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user # <-- НОВЫЕ ИМПОРТЫ

# 2. Настраиваем приложение
app = Flask(__name__)
# Устанавливаем секретный ключ для защиты сессий (ОЧЕНЬ ВАЖНО)
app.config['SECRET_KEY'] = 'rjlh5n-8mflk8gj4345.f5n78gkj94-,nff' # <-- НОВАЯ НАСТРОЙКА

# Инициализируем LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Куда перенаправлять пользователя, если он не авторизован
login_manager.login_view = 'login' 
# Сообщение, которое появится, если пользователь пытается зайти без логина
login_manager.login_message = 'Для доступа к этой странице необходимо авторизоваться.'

# Проверяем, существует ли переменная окружения DATABASE_URL, которую установит Render
DATABASE_URL = os.environ.get('DATABASE_URL') 

if DATABASE_URL:
    # Если мы на Render, используем PostgreSQL
    # 'postgres://' нужно заменить на 'postgresql+psycopg2://' для SQLAlchemy
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Если мы на вашем компьютере, используем SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///residents.db'

# Отключаем ненужное уведомление
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Создаем объект базы данных
db = SQLAlchemy(app)

# app.py

# 3. Определяем модель Пользователя (Администратора)
# UserMixin дает нам стандартные методы, которые нужны Flask-Login
class User(db.Model, UserMixin): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False) # Будем хранить хеш пароля, а не сам пароль

    def __repr__(self):
        return f'<User: {self.username}>'

# Функция-загрузчик, необходимая Flask-Login
# Говорит, как найти пользователя по ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 3.1. Определяем, как выглядит "Жилец" (Модель данных для таблицы)
class Resident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    apartment_number = db.Column(db.String(10), unique=True, nullable=False)
    contact = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<Жилец: {self.name}, Квартира: {self.apartment_number}>'


# 4. Маршрут для главной страницы (http://127.0.0.1:5000/)
@app.route('/')
def index():
    # Получаем ВСЕХ жильцов из базы
    all_residents = Resident.query.all()
    
    # Отображаем шаблон index.html
    return render_template('index.html', жильцы=all_residents) 


# 5. Маршрут для добавления жильцов
@app.route('/add', methods=['GET', 'POST'])
@login_required # <-- ДОБАВЛЯЕМ ЭТУ СТРОКУ: требует логина для доступа!
def add_resident():
    if request.method == 'POST':
        # Если данные пришли через форму (POST)
        name_data = request.form.get('name')
        apt_data = request.form.get('apartment_number')
        contact_data = request.form.get('contact')
        
        # Создаем и сохраняем нового жильца
        new_resident = Resident(
            name=name_data,
            apartment_number=apt_data,
            contact=contact_data
        )
        db.session.add(new_resident)
        db.session.commit()
        
        # Перенаправляем на главную страницу (index)
        return redirect(url_for('index'))
        
    # Если просто зашли на страницу (GET), показываем форму
    return render_template('add_resident.html')


# 6. Маршрут для входа администратора
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже вошел, перенаправляем его на главную
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Находим пользователя по имени
        user = User.query.filter_by(username=username).first()
        
        # ВАЖНО: В реальном проекте здесь должна быть ПРОВЕРКА ХЕША ПАРОЛЯ!
        # Здесь для простоты мы просто сравниваем пароли
        if user and user.password_hash == password:
            login_user(user) # Записываем пользователя как авторизованного
            # flash('Вы успешно авторизовались!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
            
    return render_template('login.html')

# 6.1. Маршрут для выхода
@app.route('/logout')
@login_required # Только авторизованный пользователь может выйти
def logout():
    logout_user()
    # flash('Вы вышли из системы.', 'success')
    return redirect(url_for('index'))


# 7. Основная часть для запуска приложения
if __name__ == '__main__':
    with app.app_context():
        # Создаем таблицы в базе данных (включая новую таблицу User)
        db.create_all()

        # НОВЫЙ КОД ДЛЯ СОЗДАНИЯ АДМИНИСТРАТОРА
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            new_admin = User(username='admin', password_hash='12345') # Пароль для теста: 12345
            db.session.add(new_admin)
            db.session.commit()
            print("🔑 Пользователь 'admin' создан с паролем '12345'!")
        
        # Добавляем первого жильца для теста, если его нет
        first_resident = Resident.query.filter_by(apartment_number='101').first()

        if not first_resident:
            new_resident = Resident(
                name='Иванов Иван Иванович',
                apartment_number='101',
                contact='+7 900 123 45 67'
            )
            db.session.add(new_resident)
            db.session.commit()
            print("🎉 Жилец 'Иванов И.И.' успешно добавлен!")
        
    # Запускаем веб-приложение!
    print("\n* Запуск веб-сервера. Откройте: http://127.0.0.1:5000/")
    app.run(debug=True)