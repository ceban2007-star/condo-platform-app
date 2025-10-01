# -*- coding: utf-8 -*-
# app.py

import os 

# 1. Импортируем нужные инструменты (библиотеки)
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy 

# 2. Настраиваем приложение
app = Flask(__name__)

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


# 3. Определяем, как выглядит "Жилец" (Модель данных для таблицы)
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


# 6. Основная часть для запуска приложения
if __name__ == '__main__':
    # Эта часть запускается только один раз при старте
    with app.app_context():
        # Создаем таблицы в базе данных (если они еще не созданы)
        db.create_all()

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