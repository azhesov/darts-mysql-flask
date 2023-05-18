import os
import datetime
from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
# Для работы системы используется фреймворк Flask, на котором основана логика работы задней части приложения,
# фреймворк SQLAlchemy используется для работы с базой данных, реализации CRUD функций необходимых для
# функционирования приложения. Библиотека CORS необходима для получения разрешений на запросы с
# фронтальной части приложения. Данная версия задней части приложения является промежуточной/экспериментальной,
# тк в ней реализована работа с базой данных, а также получение/отображение информации на Flask фронтальной части
# и получение/отсылка информации на React фронтальную часть

basedir = os.path.abspath(os.path.dirname(__file__))
# Конфигурация папки UPLOAD_FOLDER нужна для того чтобы определить место где будут храниться изображения
UPLOAD_FOLDER = os.path.join('staticFiles', 'images')

# Конфигурация приложения с определением места где будут храниться изображения и где будут находиться шаблоны для
# отображения фронтальной части приложения
app = Flask(__name__, template_folder='templates', static_folder='staticFiles')
# Конфигурация SQL базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'sqlite_darts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'Secret key'
CORS(app, support_credentials=True)

db = SQLAlchemy(app)


# Определение полей и связей класса LongRead (Лонгрид)
class LongRead(db.Model):
    __tablename__ = 'LongRead'
    id = db.Column(db.Integer, primary_key=True)
    world_id = db.Column(db.Integer, db.ForeignKey('World.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    img_link = db.Column(db.String(200), nullable=True)

    map_link = db.Column(db.String(200), nullable=True)
    time_line_link = db.Column(db.String(200), nullable=True)

    chapters = db.relationship('Chapter', backref='longread', lazy=True)
    blockcontents = db.relationship('BlockContent', backref='longread', lazy=True)

    def __repr__(self):
        return f'<LongRead {self.name}>'


# Функция для передачи на React фронтальную часть приложения всех лонгридов находящихся в базе данных
@app.route('/api/explore/')
def api_longread_index():
    # Получение списка всех лонгридов по запросу в базу данных
    longreads = LongRead.query.all()
    # JSON-текст в котором указаны данные лонгрида
    longreads_data = [{'id': longread.id,
                       'name': longread.name,
                       'img_link': 'http://127.0.0.1:5000' + longread.img_link,
                       'description': longread.description} for longread in longreads]
    # JSON-текст перенаправляется на фронтальную часть приложения
    return jsonify(longreads_data), 200


# Функция для передачи на Flask фронтальную часть приложения всех лонгридов находящихся в базе данных
@app.route('/explore/')
def longread_index():
    # Получение списка всех лонгридов по запросу в базу данных
    longreads = LongRead.query.all()
    # Отсылка собранных данных на фронтальную часть приложения для их отображения
    return render_template('longread_index.html', longreads=longreads)


# Функция для передачи на React фронтальную часть приложения информации о лонгриде по его индексу,
# а также информации о всех связанных с ним глав
@app.route('/api/longreads/<int:longread_id>', methods=['GET'])
def api_longread(longread_id):
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    # Получение списка глав по запросу в базу данных, связанных с лонгридом
    chapters = Chapter.query.filter(Chapter.longread_id == longread_id).all()
    # Формирование JSON-текста с данными о главах связанных с лонгридом
    chapter_data = [{'id': chapter.id,
                     'name': chapter.name,
                     'longread_id': chapter.longread_id} for chapter in chapters]
    # Формирование JSON-текста с данными лонгрида и главами
    longread_data = {
        'id': longread.id,
        'name': longread.name,
        'description': longread.description,
        'img_link': 'http://127.0.0.1:5000' + longread.img_link,
        'chapters': chapter_data
    }
    # JSON-текст перенаправляется на фронтальную часть приложения
    return jsonify(longread_data), 200


# Функция для передачи на Flask фронтальную часть приложения информации о лонгриде по его индексу,
# а также информации о всех связанных с ним глав
@app.route('/longreads/<int:longread_id>/')
def longread(longread_id):
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    # Получение списка глав по запросу в базу данных, связанных с лонгридам
    chapters = Chapter.query.filter(Chapter.longread_id == longread_id).all()
    # Отсылка собранных данных на фронтальную часть приложения для их отображения
    return render_template('longread.html', longread=longread, chapters=chapters)


# React Функция для создания лонгрида и привязки его к миру, идентификатор которого был указан.
# При создании лонгрида ему будет присвоена стандартная фотография
@app.route('/api/worlds/<int:world_id>/create/', methods=('GET', 'OPTIONS', 'POST'))
def api_longread_create(world_id):
    # Фронтальная часть приложения перед отправлением запроса на создание элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    #Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Создание лонгрида используя данные полученные из JSON-текста
    longread = LongRead(world_id=world_id,
                        name=json["name"],
                        description=json["description"])
    # Лонгриду присваивается стандартная фотография
    longread.img_link = "/staticFiles/images/QuestionMark.jpg"
    # Добавление нового лонгрида в сессию изменений
    db.session.add(longread)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Longread created successfully'}), 201


# Flask Функция для создания лонгрида и привязки его к миру, идентификатор которого был указан.
# При создании лонгрида ему будет присвоена стандартная фотография, либо фотография загруженная в форму
@app.route('/worlds/<int:world_id>/create/', methods=('GET', 'POST'))
def longread_create(world_id):
    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        name = request.form['name']
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        # Создание лонгрида используя данные полученные из форм
        longread = LongRead(world_id=world_id,
                            name=name,
                            description=description)
        # Добавление нового лонгрида в сессию изменений
        db.session.add(longread)
        # Использование функции flush для получения id нового лонгрида
        db.session.flush()
        # Обновление лонгрида для получения id
        db.session.refresh(longread)
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename == '':
            # Если пустой файл лонгриду присваивается стандартная фотография
            longread.img_link = "/staticFiles/images/QuestionMark.jpg"
        else:
            # Создание уникального имени использую id лонгрида
            longread_img_name = "longread" + str(longread.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name))
            # Сохранение названия файла
            longread.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('create_longread.html', world_id=world_id)


# React Функция для редактирования лонгрида, идентификатор которого был указан
@app.route('/api/longreads/<int:longread_id>/edit/', methods=['GET', 'POST', 'OPTIONS'])
def api_longread_edit(longread_id):
    # Фронтальная часть приложения перед отправлением запроса на редактирование элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    # Внесение изменений
    longread.name = json["name"]
    longread.description = json["description"]
    # Добавление измененного лонгрида в сессию изменений
    db.session.add(longread)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Longread updated successfully'})


# Flask Функция для редактирования лонгрида и его фотографии, используя указанный идентификатор лонгрида. Предыдущее
# изображение лонгрида будет удалено, если оно не являлось стандартным
@app.route('/longreads/<int:longread_id>/edit/', methods=('GET', 'POST'))
def longread_edit(longread_id):
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    longread_id = longread.id
    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        name = request.form['name']
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename != '':
            # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
            if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
                # Удаление фотографии
                os.remove(longread.img_link[1:])
            # Создание уникального имени использую id лонгрида
            longread_img_name = "longread" + str(longread.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name))
            # Внесение изменений
            longread.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name)
        # Внесение изменений
        longread.name = name
        longread.description = description
        # Добавление измененного лонгрида в сессию изменений
        db.session.add(longread)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('longread', longread_id=longread_id))

    return render_template('edit_longread.html', longread=longread)


# React Функция для измененения фотографии лонгрида, идентификатор которого был указан. Предыдущее изображение
# лонгрида будет удалено, если оно не являлось стандартным
@app.route('/api/longreads/<int:longread_id>/update-image/', methods=['GET', 'OPTIONS', 'POST'])
def api_update_longread_image(longread_id):
    # Фронтальная часть приложения перед отправлением запроса на изменение изображения привязанного к элементу
    # отправляет OPTIONS запрос, на который необходимо ответить ответом с необходимыми заголовками, в котором
    # указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    # Получение файла изображения из формы
    new = request.files["image"]
    # Сохранение названия файла
    filename = new.filename
    # Проверка на пустой файл
    if filename != '':
        # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
        if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
            # Удаление фотографии
            os.remove(longread.img_link[1:])
        # Создание уникального имени использую id лонгрида
        longread_img_name = "longread" + str(longread.id) + ".jpg"
        # Сохранение изображения в папку под уникальным именем
        new.save(os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name))
        # Внесение изменений
        longread.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name)
    # Добавление измененного лонгрида в сессию изменений
    db.session.add(longread)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Longread updated successfully'})


# Flask Функция для удаления фотографии лонгрида, идентификатор которого был указан. Изображение
# лонгрида будет удалено, если оно не являлось стандартным
@app.post('/longreads/<int:longread_id>/delete_longread_image/')
def delete_longread_image(longread_id):
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(longread.img_link[1:])
        # Лонгриду присваивается стандартная фотография
        longread.img_link = "/staticFiles/images/QuestionMark.jpg"
        # Добавление измененного лонгрида в сессию изменений
        db.session.add(longread)
        # Фиксация изменений в БД
        db.session.commit()
    return redirect(url_for('longread', longread_id=longread_id))


# React Функция для удаления лонгрида, указанного по его идентификатору, а также всех глав и изображения,
# которое с ним связано
@app.route('/api/longreads/<int:longread_id>/delete/', methods=('GET', 'OPTIONS', 'DELETE'))
def api_longread_delete(longread_id):
    # Фронтальная часть приложения перед отправлением запроса на удаление элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    # Получение списка глав по запросу в базу данных, связанных с лонгридом
    chapters = Chapter.query.filter(Chapter.longread_id == longread_id).all()
    # Удаление глав, связанных с лонгридом
    for chapter in chapters:
        chapter_delete(chapter.id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(longread.img_link[1:])
    # Удаление лонгрида
    db.session.delete(longread)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return {'message': 'Longread deleted successfully'}


# Flask Функция для удаления лонгрида, указанного по его идентификатору, а также всех глав и изображения,
# которое с ним связано
@app.post('/longreads/<int:longread_id>/delete/')
def longread_delete(longread_id):
    # Получение лонгрида по запросу в базу данных
    longread = LongRead.query.get_or_404(longread_id)
    world_id = longread.world_id
    # Получение списка глав по запросу в базу данных, связанных с лонгридом
    chapters = Chapter.query.filter(Chapter.longread_id == longread_id).all()
    # Удаление глав, связанных с лонгридом
    for chapter in chapters:
        chapter_delete(chapter.id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(longread.img_link[1:])
    # Удаление лонгрида
    db.session.delete(longread)
    # Фиксация изменений в БД
    db.session.commit()
    return redirect(url_for('world', world_id=world_id))


# Определение полей и связей класса Chapter (Глава)
class Chapter(db.Model):
    __tablename__ = 'Chapter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    longread_id = db.Column(db.Integer, db.ForeignKey('LongRead.id'), nullable=False)

    blockcontents = db.relationship('BlockContent', backref='chapter', lazy=True)

    def __repr__(self):
        return f'<Chapter {self.name}>'


# Функция для передачи на React фронтальную часть приложения информации о главе по ее индексу,
# а также информации о всех связанных с ней контент блоков
@app.route('/api/chapter/<int:chapter_id>', methods=['GET'])
def api_chapter(chapter_id):
    # Получение главы по запросу в базу данных
    chapter = Chapter.query.get_or_404(chapter_id)
    # Получение списка контент блоков по запросу в базу данных, связанных с главой
    blockcontents = BlockContent.query.filter(BlockContent.chapter_id == chapter_id,
                                              BlockContent.longread_id == chapter.longread_id).all()
    # Формирование JSON-текста с данными о контент блоках связанных с главой
    blockcontents_data = [{'id': blockcontent.id,
                           'longread_id': blockcontent.longread_id,
                           'chapter_id': blockcontent.chapter_id,
                           'text': blockcontent.text,
                           'img_link': 'http://127.0.0.1:5000' + blockcontent.img_link} for blockcontent in
                          blockcontents]
    # Формирование JSON-текста с данными главы и контент блоками
    chapter_data = {
        'id': chapter.id,
        'name': chapter.name,
        'longread_id': chapter.longread_id,
        'blockcontents': blockcontents_data
    }
    # JSON-текст перенаправляется на фронтальную часть приложения
    return jsonify(chapter_data), 200


# Функция для передачи на Flask фронтальную часть приложения информации о главе по ее индексу,
# а также информации о всех связанных с ней контент блоков
@app.route('/chapter/<int:chapter_id>/')
def chapter(chapter_id):
    # Получение главы по запросу в базу данных
    chapter = Chapter.query.get_or_404(chapter_id)
    # Получение списка контент блоков по запросу в базу данных, связанных с главой
    blockcontents = BlockContent.query.filter(BlockContent.chapter_id == chapter_id,
                                              BlockContent.longread_id == chapter.longread_id).all()
    # Отсылка собранных данных на фронтальную часть приложения для их отображения
    return render_template('chapter.html', chapter=chapter, blockcontents=blockcontents)


# React Функция для создания главы и привязки ее к лонгриду, идентификатор которого был указан.
# При создании главы ей будет присвоена стандартная фотография.
@app.route('/api/longreads/<int:longread_id>/create/', methods=('GET', 'OPTIONS', 'POST'))
def api_chapter_create(longread_id):
    # Фронтальная часть приложения перед отправлением запроса на создание элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    #Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Создание главы используя данные полученные из JSON-текста
    chapter = Chapter(longread_id=longread_id,
                      name=json["name"])
    # Добавление главы в сессию изменений
    db.session.add(chapter)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Chapter created successfully'}), 201


# Flask Функция для создания главы и привязки ее к лонгриду, идентификатор которого был указан.
# При создании главы ей будет присвоена стандартная фотография, либо фотография загруженная в форму
@app.route('/longreads/<int:longread_id>/create/', methods=('GET', 'POST'))
def chapter_create(longread_id):
    if request.method == 'POST':
        # Получение данных из формы
        name = request.form['name']
        # Создание главы используя данные полученные из формы
        chapter = Chapter(name=name, longread_id=longread_id)
        # Добавление главы в сессию изменений
        db.session.add(chapter)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('longread', longread_id=longread_id))

    return render_template('create_chapter.html', longread_id=longread_id)


# React Функция для редактирования главы, используя указанный идентификатор главы
@app.route('/api/chapter/<int:chapter_id>/edit/', methods=['GET', 'POST', 'OPTIONS'])
def api_chapter_edit(chapter_id):
    # Фронтальная часть приложения перед отправлением запроса на редактирование элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Получение главы по запросу в базу данных
    chapter = Chapter.query.get_or_404(chapter_id)
    # Внесение изменений
    chapter.name = json["name"]
    # Добавление измененной главы в сессию изменений
    db.session.add(chapter)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Chapter updated successfully'})


# Flask Функция для редактирования главы, используя указанный идентификатор главы
@app.route('/chapter/<int:chapter_id>/edit/', methods=('GET', 'POST'))
def chapter_edit(chapter_id):
    # Получение объекта главы по запросу в базу данных
    chapter = Chapter.query.get_or_404(chapter_id)
    longread_id = chapter.longread_id
    if request.method == 'POST':
        # Получение данных из формы
        name = request.form['name']
        # Внесение изменений
        chapter.name = name
        chapter.longread_id = longread_id
        # Добавление измененной главы в сессию изменений
        db.session.add(chapter)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('chapter', chapter_id=chapter_id))

    return render_template('edit_chapter.html', chapter=chapter)


# React Функция для удаления главы, указанной по ее идентификатору,
# а также всех контент блоков, которые с ней связаны
@app.route('/api/chapter/<int:chapter_id>/delete/', methods=('GET', 'OPTIONS', 'DELETE'))
def api_chapter_delete(chapter_id):
    # Фронтальная часть приложения перед отправлением запроса на удаление элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение главы по запросу в базу данных
    chapter = Chapter.query.get_or_404(chapter_id)
    # Получение списка контент блоков по запросу в базу данных, связанных с главой
    blockcontents = BlockContent.query.filter(BlockContent.chapter_id == chapter_id,
                                              BlockContent.longread_id == chapter.longread_id).all()
    # Удаление контент блоков, связанных с главой
    for blockcontent in blockcontents:
        blockcontent_delete(blockcontent.id)
    # Удаление главы
    db.session.delete(chapter)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return {'message': 'Chapter deleted successfully'}


# Flask Функция для удаления главы, указанной по ее идентификатору,
# а также всех контент блоков, которые с ней связаны
@app.post('/chapter/<int:chapter_id>/delete/')
def chapter_delete(chapter_id):
    # Получение главы по запросу в базу данных
    chapter = Chapter.query.get_or_404(chapter_id)
    longread_id = chapter.longread_id
    # Получение списка контент блоков по запросу в базу данных, связанных с главой
    blockcontents = BlockContent.query.filter(BlockContent.chapter_id == chapter_id,
                                              BlockContent.longread_id == chapter.longread_id).all()
    # Удаление контент блоков, связанных с главой
    for blockcontent in blockcontents:
        blockcontent_delete(blockcontent.id)
    # Удаление главы
    db.session.delete(chapter)
    # Фиксация изменений в БД
    db.session.commit()
    return redirect(url_for('longread', longread_id=longread_id))


# Определение полей и связей класса BlockContent (Контент блок)
class BlockContent(db.Model):
    __tablename__ = 'BlockContent'
    id = db.Column(db.Integer, primary_key=True)
    longread_id = db.Column(db.Integer, db.ForeignKey('LongRead.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('Chapter.id'), nullable=False)
    text = db.Column(db.String(10000), nullable=True)
    img_link = db.Column(db.String(200), nullable=True)

    coordx = db.Column(db.Integer, nullable=True)
    coordy = db.Column(db.Integer, nullable=True)
    time = db.Column(db.DateTime(timezone=True), nullable=True)
    floating_text = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<BlockContent {self.name}>'


# React Функция для создания контент блока и привязки его к главе, идентификатор которой был указан.
# При создании контент блока ему будет присвоена стандартная фотография
@app.route('/api/blockcontent/<int:longread_id>/<int:chapter_id>/create/', methods=('GET', 'OPTIONS', 'POST'))
def api_blockcontent_create(longread_id, chapter_id):
    # Фронтальная часть приложения перед отправлением запроса на создание элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    #Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Создание контент блока используя данные полученные из JSON-текста
    blockcontent = BlockContent(longread_id=longread_id,
                                chapter_id=chapter_id,
                                text=json["text"])
    # Контент блоку присваивается стандартная фотография
    blockcontent.img_link = "/staticFiles/images/font.jpg"
    # Добавление контент блока в сессию изменений
    db.session.add(blockcontent)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Blockcontent created successfully'}), 201


# Flask Функция для создания контент блока и привязки его к главе, идентификатор которой был указан.
# При создании контент блока ему будет присвоена стандартная фотография, либо фотография загруженная в форму
@app.route('/blockcontent/<int:longread_id>/<int:chapter_id>/create/', methods=('GET', 'POST'))
def blockcontent_create(longread_id, chapter_id):
    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        text = request.form['text']
        uploaded_img = request.files['uploaded-file']
        # Создание контент блока используя данные полученные из формы
        blockcontent = BlockContent(longread_id=longread_id,
                                    chapter_id=chapter_id,
                                    text=text)
        # Добавление контент блока в сессию изменений
        db.session.add(blockcontent)
        # Использование функции flush для получения id нового контент блока
        db.session.flush()
        # Обновление контент блока для получения id
        db.session.refresh(blockcontent)
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename == '':
            # Если пустой файл контент блоку присваивается стандартная фотография
            blockcontent.img_link = "/staticFiles/images/font.jpg"
        else:
            # Создание уникального имени использую id контент блока
            blockcontent_img_name = "blockcontent" + str(blockcontent.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name))
            # Сохранение названия файла
            blockcontent.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name)
        # Фиксация изменений в БД
        db.session.commit()
        return redirect(url_for('chapter', chapter_id=chapter_id))

    return render_template('create_blockcontent.html', chapter_id=chapter_id)


# React Функция для редактирования контент блока, используя указанный идентификатор контент блока.
@app.route('/api/blockcontent/<int:blockcontent_id>/edit/', methods=['GET', 'POST', 'OPTIONS'])
def api_blockcontent_edit(blockcontent_id):
    # Фронтальная часть приложения перед отправлением запроса на редактирование элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Получение контент блока по запросу в базу данных
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    # Внесение изменений
    blockcontent.text = json["text"]
    # Добавление измененного контент блока в сессию изменений
    db.session.add(blockcontent)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Blockcontent updated successfully'})


# Flask Функция для редактирования контент блока и его фотографии, используя указанный идентификатор контент блока.
# Предыдущее изображение контент блока будет удалено, если оно не являлось стандартным
@app.route('/blockcontent/<int:blockcontent_id>/edit/', methods=('GET', 'POST'))
def blockcontent_edit(blockcontent_id):
    # Получение контент блока по запросу в базу данных
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    chapter_id = blockcontent.chapter_id
    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        text = request.form['text']
        uploaded_img = request.files['uploaded-file']
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename != '':
            # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
            if blockcontent.img_link != "/staticFiles/images/font.jpg":
                # Удаление фотографии
                os.remove(blockcontent.img_link[1:])
            # Создание уникального имени использую id контент блока
            blockcontent_img_name = "blockcontent" + str(blockcontent.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name))
            # Внесение изменений
            blockcontent.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name)
        # Внесение изменений
        blockcontent.text = text
        # Добавление измененного контент блока в сессию изменений
        db.session.add(blockcontent)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('chapter', chapter_id=chapter_id))

    return render_template('edit_blockcontent.html', blockcontent=blockcontent)


# React Функция для измененения фотографии контент блока, идентификатор которого был указан. Предыдущее изображение
# контент блока будет удалено, если оно не являлось стандартным
@app.route('/api/blockcontent/<int:blockcontent_id>/update-image/', methods=['GET', 'OPTIONS', 'POST'])
def api_update_blockcontent_image(blockcontent_id):
    # Фронтальная часть приложения перед отправлением запроса на изменение изображения привязанного к элементу
    # отправляет OPTIONS запрос, на который необходимо ответить ответом с необходимыми заголовками, в котором
    # указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение контент блока по запросу в базу данных
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    # Получение файла изображения из формы
    new = request.files["image"]
    # Сохранение названия файла
    filename = new.filename
    # Проверка на пустой файл
    if filename != '':
        # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
        if blockcontent.img_link != "/staticFiles/images/font.jpg":
            # Удаление фотографии
            os.remove(blockcontent.img_link[1:])
        # Создание уникального имени использую id контент блока
        blockcontent_img_name = "blockcontent" + str(blockcontent.id) + ".jpg"
        # Сохранение изображения в папку под уникальным именем
        new.save(os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name))
        # Внесение изменений
        blockcontent.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name)
    # Добавление измененного контент блока в сессию изменений
    db.session.add(blockcontent)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'Blockcontent updated successfully'})


# Flask Функция для удаления фотографии контент блока, идентификатор которого был указан. Изображение
# контент блока будет удалено, если оно не являлось стандартным
@app.post('/blockcontent/<int:blockcontent_id>/delete_blockcontent_image/')
def delete_blockcontent_image(blockcontent_id):
    # Получение контент блока по запросу в базу данных
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if blockcontent.img_link != "/staticFiles/images/font.jpg":
        # Удаление фотографии
        os.remove(blockcontent.img_link[1:])
        blockcontent.img_link = "/staticFiles/images/font.jpg"
        # Добавление измененного контент блока в сессию изменений
        db.session.add(blockcontent)
        # Фиксация изменений в БД
        db.session.commit()
    return redirect(url_for('chapter', chapter_id=blockcontent.chapter_id))


# React Функция для удаления контент блока, указанного по его идентификатору, а также изображения,
# которое с ним связано
@app.route('/api/blockcontent/<int:blockcontent_id>/delete/', methods=('GET', 'OPTIONS', 'DELETE'))
def api_blockcontent_delete(blockcontent_id):
    # Фронтальная часть приложения перед отправлением запроса на удаление элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение контент блока по запросу в базу данных
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if blockcontent.img_link != "/staticFiles/images/font.jpg":
        # Удаление фотографии
        os.remove(blockcontent.img_link[1:])
    # Удаление контент блока
    db.session.delete(blockcontent)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return {'message': 'Blockcontent deleted successfully'}


# Flask Функция для удаления контент блока, указанного по его идентификатору, а также
# изображения, которое с ним связано
@app.post('/blockcontent/<int:blockcontent_id>/delete/')
def blockcontent_delete(blockcontent_id):
    # Получение контент блока по запросу в базу данных
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    chapter_id = blockcontent.chapter_id
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if blockcontent.img_link != "/staticFiles/images/font.jpg":
        # Удаление фотографии
        os.remove(blockcontent.img_link[1:])
    # Удаление контент блока
    db.session.delete(blockcontent)
    # Фиксация изменений в БД
    db.session.commit()
    return redirect(url_for('chapter', chapter_id=chapter_id))


# Определение полей и связей класса World (Мир)
class World(db.Model):
    __tablename__ = 'World'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    img_link = db.Column(db.String(200), nullable=True)
    description = db.Column(db.String(10000), nullable=False)

    longreads = db.relationship('LongRead', backref='world', lazy=True)
    worldodjs = db.relationship('WorldObj', backref='world', lazy=True)

    def __repr__(self):
        return f'<World {self.name}>'


# Функция для передачи на React фронтальную часть приложения всех миров находящихся в базе данных, функция
# дублирует ответ, который отправляется функцией api_world_index однако может быть переопределена по запросу коллег из
# фронтальной части приложения, для отображения других данных на индексной странице приложения
@app.route('/api/')
def api_index():
    # Получение списка всех миров по запросу в базу данных
    worlds = World.query.all()
    # JSON-текст в котором указаны данные мира
    worlds_data = [{'id': world.id,
                    'name': world.name,
                    'img_link': 'http://127.0.0.1:5000' + world.img_link,
                    'description': world.description} for world in worlds]
    # JSON-текст перенаправляется на фронтальную часть приложения
    return jsonify(worlds_data), 200


# Функция для передачи на Flask фронтальную часть приложения всех миров находящихся в базе данных, функция
# дублирует ответ, который отправляется функцией world_index
@app.route('/')
def index():
    # Получение списка всех миров по запросу в базу данных
    worlds = World.query.all()
    # Отсылка собранных данных на фронтальную часть приложения для их отображения
    return render_template('world_index.html', worlds=worlds)


# Функция для передачи на React фронтальную часть приложения всех миров находящихся в базе данных
@app.route('/api/worlds/')
def api_world_index():
    # Получение списка всех миров по запросу в базу данных
    worlds = World.query.all()
    # JSON-текст в котором указаны данные мира
    worlds_data = [{'id': world.id,
                    'name': world.name,
                    'img_link': 'http://127.0.0.1:5000' + world.img_link,
                    'description': world.description} for world in worlds]
    # JSON-текст перенаправляется на фронтальную часть приложения
    return jsonify(worlds_data), 200


# Функция для передачи на Flask фронтальную часть приложения всех миров находящихся в базе данных
@app.route('/worlds/')
def world_index():
    # Получение списка всех миров по запросу в базу данных
    worlds = World.query.all()
    # Отсылка собранных данных на фронтальную часть приложения для их отображения
    return render_template('world_index.html', worlds=worlds)


# Функция для передачи на React фронтальную часть приложения информации о мире по его индексу,
# а также информации о всех связанных с ним лонгридов и объектов мира
@app.route('/api/worlds/<int:world_id>', methods=['GET'])
def api_world(world_id):
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    # Получение списка лонгридов по запросу в базу данных, связанных с миром
    longreads = LongRead.query.filter(LongRead.world_id == world_id).all()
    # Получение списка объектов мира по запросу в базу данных, связанных с миром
    worldobjs = WorldObj.query.filter(WorldObj.world_id == world_id).all()
    # Формирование JSON-текста с данными о лонгридах связанных с миром
    longreads_data = [{'id': longread.id,
                       'world_id': longread.world_id,
                       'name': longread.name,
                       'description': longread.description,
                       'img_link': 'http://127.0.0.1:5000' + longread.img_link} for longread in longreads]
    # Формирование JSON-текста с данными о лонгридах связанных с миром
    worldobjs_data = [{'id': worldobj.id,
                       'world_id': worldobj.world_id,
                       'description': worldobj.description,
                       'img_link': 'http://127.0.0.1:5000' + worldobj.img_link} for worldobj in worldobjs]
    # Формирование JSON-текста с данными мира, лонгридами и главами
    world_data = {
        'id': world.id,
        'name': world.name,
        'description': world.description,
        'img_link': 'http://127.0.0.1:5000' + world.img_link,
        'longreads': longreads_data,
        'worldobjs': worldobjs_data
    }
    # JSON-текст перенаправляется на фронтальную часть приложения
    return jsonify(world_data), 200


# Функция для передачи на Flask фронтальную часть приложения информации о мире по его индексу,
# а также информации о всех связанных с ним лонгридов и объектов мира
@app.route('/worlds/<int:world_id>/')
def world(world_id):
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    # Получение списка лонгридов по запросу в базу данных, связанных с миром
    longreads = LongRead.query.filter(LongRead.world_id == world_id).all()
    # Получение списка объектов мира по запросу в базу данных, связанных с миром
    worldobjs = WorldObj.query.filter(WorldObj.world_id == world_id).all()
    # Отсылка собранных данных на фронтальную часть приложения для их отображения
    return render_template('world.html', world=world, longreads=longreads, worldobjs=worldobjs)


# React Функция для создания мира, идентификатор которого был указан.
# При создании мира ему будет присвоена стандартная фотография
@app.route('/api/worlds/create/', methods=('GET', 'OPTIONS', 'POST'))
def api_world_create():
    # Фронтальная часть приложения перед отправлением запроса на создание элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    #Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Создание мира используя данные полученные из JSON-текста
    world = World(name=json["name"],
                  description=json["description"])
    # Миру присваивается стандартная фотография
    world.img_link = "/staticFiles/images/QuestionMark.jpg"
    # Добавление нового мира в сессию изменений
    db.session.add(world)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'World created successfully'}), 201


# Flask Функция для создания мира, идентификатор которого был указан.
# При создании мира ему будет присвоена стандартная фотография, либо фотография загруженная в форму
@app.route('/worlds/create/', methods=('GET', 'POST'))
def world_create():
    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        name = request.form['name']
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        # Создание мира используя данные полученные из форм
        world = World(name=name,
                      description=description)
        # Добавление нового мира в сессию изменений
        db.session.add(world)
        # Использование функции flush для получения id нового мира
        db.session.flush()
        # Обновление мира для получения id
        db.session.refresh(world)
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename == '':
            # Если пустой файл миру присваивается стандартная фотография
            world.img_link = "/staticFiles/images/QuestionMark.jpg"
        else:
            # Создание уникального имени использую id мира
            world_img_name = "world" + str(world.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], world_img_name))
            # Сохранение названия файла
            world.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], world_img_name)
        # Фиксация изменений в БД
        db.session.commit()
        return redirect(url_for('world_index'))

    return render_template('create_world.html')


# React Функция для редактирования мира, идентификатор которого был указан
@app.route('/api/worlds/<int:world_id>/edit/', methods=['GET', 'POST', 'OPTIONS'])
def api_world_edit(world_id):
    # Фронтальная часть приложения перед отправлением запроса на редактирование элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    # Внесение изменений
    world.name = json["name"]
    world.description = json["description"]
    # Добавление измененного мира в сессию изменений
    db.session.add(world)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'World updated successfully'})


# Flask Функция для редактирования мира и его фотографии, используя указанный идентификатор мира. Предыдущее
# изображение мира будет удалено, если оно не являлось стандартным
@app.route('/worlds/<int:world_id>/edit/', methods=('GET', 'POST'))
def world_edit(world_id):
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    world_id = world.id

    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        name = request.form['name']
        uploaded_img = request.files['uploaded-file']
        description = request.form['description']
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename != '':
            # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
            if world.img_link != "/staticFiles/images/QuestionMark.jpg":
                # Удаление фотографии
                os.remove(world.img_link[1:])
            # Создание уникального имени использую id мира
            world_img_name = "world" + str(world.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], world_img_name))
            # Внесение изменений
            world.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], world_img_name)
        # Внесение изменений
        world.name = name
        world.description = description
        # Добавление измененного мира в сессию изменений
        db.session.add(world)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('edit_world.html', world=world)


# React Функция для изменения фотография мира, идентификатор которого был указан.
# Предыдущее изображение мира будет удалено, если оно не являлось стандартным
@app.route('/api/worlds/<int:world_id>/update-image/', methods=['GET', 'OPTIONS', 'POST'])
def api_update_world_image(world_id):
    # Фронтальная часть приложения перед отправлением запроса на изменение изображения привязанного к элементу
    # отправляет OPTIONS запрос, на который необходимо ответить ответом с необходимыми заголовками, в котором
    # указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    # Получение файла изображения из формы
    new = request.files["image"]
    # Сохранение названия файла
    filename = new.filename
    # Проверка на пустой файл
    if filename != '':
        # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
        if world.img_link != "/staticFiles/images/QuestionMark.jpg":
            # Удаление фотографии
            os.remove(world.img_link[1:])
        # Создание уникального имени использую id мира
        world_img_name = "world" + str(world.id) + ".jpg"
        # Сохранение изображения в папку под уникальным именем
        new.save(os.path.join(app.config['UPLOAD_FOLDER'], world_img_name))
        # Внесение изменений
        world.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], world_img_name)
    # Добавление измененного мира в сессию изменений
    db.session.add(world)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'World updated successfully'})


# Flask Функция для удаления фотографии мира, идентификатор которого был указан. Изображение
# мира будет удалено, если оно не являлось стандартным
@app.post('/worlds/<int:world_id>/delete_world_image/')
def delete_world_image(world_id):
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if world.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(world.img_link[1:])
        # Миру присваивается стандартная фотография
        world.img_link = "/staticFiles/images/QuestionMark.jpg"
        # Добавление измененного мира в сессию изменений
        db.session.add(world)
        # Фиксация изменений в БД
        db.session.commit()
    return redirect(url_for('world', world_id=world_id))


# React Функция для удаления мира, указанного по ее идентификатору, а также изображения, всех лонгридов и
# объектов мира, которые с ним связаны
@app.route('/api/worlds/<int:world_id>/delete/', methods=('GET', 'OPTIONS', 'DELETE'))
def api_world_delete(world_id):
    # Фронтальная часть приложения перед отправлением запроса на удаление элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    # Получение списка лонгридов по запросу в базу данных, связанных с миром
    longreads = LongRead.query.filter(LongRead.world_id == world_id).all()
    # Получение списка объектов мира по запросу в базу данных, связанных с миром
    worldobjs = WorldObj.query.filter(WorldObj.world_id == world_id).all()
    # Удаление лонгридов, связанных с миром
    for longread in longreads:
        longread_delete(longread.id)
    # Удаление объектов мира, связанных с миром
    for worldobj in worldobjs:
        worldobj_delete(worldobj.id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if world.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(world.img_link[1:])
    # Удаление мира
    db.session.delete(world)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return {'message': 'World deleted successfully'}


# Flask Функция для удаления мира, указанного по ее идентификатору, а также изображения, всех лонгридов и
# объектов мира, которые с ним связаны
@app.post('/worlds/<int:world_id>/delete/')
def world_delete(world_id):
    # Получение мира по запросу в базу данных
    world = World.query.get_or_404(world_id)
    # Получение списка лонгридов по запросу в базу данных, связанных с миром
    longreads = LongRead.query.filter(LongRead.world_id == world_id).all()
    # Получение списка объектов мира по запросу в базу данных, связанных с миром
    worldobjs = WorldObj.query.filter(WorldObj.world_id == world_id).all()
    # Удаление лонгридов, связанных с миром
    for longread in longreads:
        longread_delete(longread.id)
    # Удаление объектов мира, связанных с миром
    for worldobj in worldobjs:
        worldobj_delete(worldobj.id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if world.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(world.img_link[1:])
    # Удаление мира
    db.session.delete(world)
    # Фиксация изменений в БД
    db.session.commit()
    return redirect(url_for('world_index'))


blockcontents = db.Table('blockcontents',
                         db.Column('blockcontent_id', db.Integer, db.ForeignKey('BlockContent.id'), primary_key=True),
                         db.Column('worldobj_id', db.Integer, db.ForeignKey('WorldObj.id'), primary_key=True)
                         )


# Определение полей и связей класса WorldObj (Объект мира)
class WorldObj(db.Model):
    __tablename__ = 'WorldObj'
    id = db.Column(db.Integer, primary_key=True)
    world_id = db.Column(db.Integer, db.ForeignKey('World.id'), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    img_link = db.Column(db.String(200), nullable=True)

    blockcontents = db.relationship('BlockContent',
                                    secondary=blockcontents,
                                    lazy='subquery',
                                    backref=db.backref('worldobj', lazy=True))

    def __repr__(self):
        return f'<WorldObj {self.name}>'


# React Функция для создания объекта мира. При создании объекта мира ему будет присвоена стандартная фотография
@app.route('/api/worlds/<int:world_id>/create_worldobj/', methods=('GET', 'OPTIONS', 'POST'))
def api_worldobj_create(world_id):
    # Фронтальная часть приложения перед отправлением запроса на создание элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    #Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Создание объекта мира используя данные полученные из JSON-текста
    worldobj = WorldObj(world_id=world_id,
                        description=json["description"])
    # Объекту мира присваивается стандартная фотография
    worldobj.img_link = "/staticFiles/images/QuestionMark.jpg"
    # Добавление нового объекта мира в сессию изменений
    db.session.add(worldobj)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'WorldObj created successfully'}), 201


# Flask Функция для создания объекта мира, идентификатор которого был указан.
# При создании объекта мира ему будет присвоена стандартная фотография, либо фотография загруженная в форму
@app.route('/worlds/<int:world_id>/create_worldobj/', methods=('GET', 'POST'))
def worldobj_create(world_id):
    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        # Создание объекта мира используя данные полученные из форм
        worldobj = WorldObj(world_id=world_id,
                            description=description)
        # Добавление нового объекта мира в сессию изменений
        db.session.add(worldobj)
        # Использование функции flush для получения id нового объекта мира
        db.session.flush()
        # Обновление объекта мира для получения id
        db.session.refresh(worldobj)
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename == '':
            # Если пустой файл объекту мира присваивается стандартная фотография
            worldobj.img_link = "/staticFiles/images/QuestionMark.jpg"
        else:
            # Создание уникального имени использую id объекта мира
            worldobj_img_name = "worldobj" + str(worldobj.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name))
            # Сохранение названия файла
            worldobj.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('create_worldobj.html', world_id=world_id)


# React Функция для редактирования объекта мира, идентификатор которого был указан
@app.route('/api/worldobj/<int:worldobj_id>/edit/', methods=['GET', 'POST', 'OPTIONS'])
def api_worldobj_edit(worldobj_id):
    # Фронтальная часть приложения перед отправлением запроса на редактирование элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Полученный JSON-текст парсится для извлечения из него данных
    json = request.json
    # Получение мира по запросу в базу данных
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    # Внесение изменений
    worldobj.description = json["description"]
    # Добавление измененного объекта мира в сессию изменений
    db.session.add(worldobj)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'WorldObj updated successfully'})


# Flask Функция для редактирования объекта мира и его фотографии, используя указанный идентификатор мира. Предыдущее
# изображение объекта мира будет удалено, если оно не являлось стандартным
@app.route('/worldobj/<int:worldobj_id>/edit/', methods=('GET', 'POST'))
def worldobj_edit(worldobj_id):
    # Получение объекта мира по запросу в базу данных
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    world_id = worldobj.world_id
    if request.method == 'POST':
        # Получение файла изображения и данных из формы
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        # Сохранение названия файла
        filename = uploaded_img.filename
        # Проверка на пустой файл
        if filename != '':
            # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
            if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
                # Удаление фотографии
                os.remove(worldobj.img_link[1:])
            # Создание уникального имени использую id объекта мира
            worldobj_img_name = "worldobj" + str(worldobj.id) + ".jpg"
            # Сохранение изображения в папку под уникальным именем
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name))
            # Внесение изменений
            worldobj.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name)
        # Внесение изменений
        worldobj.description = description
        # Добавление измененного объекта мира в сессию изменений
        db.session.add(worldobj)
        # Фиксация изменений в БД
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('edit_worldobj.html', worldobj=worldobj)


# React Функция для изменения фотографии объекта мира, идентификатор которого был указан.
# Предыдущее изображение объекта мира будет удалено, если оно не являлось стандартным
@app.route('/api/worldobj/<int:worldobj_id>/update-image/', methods=['GET', 'OPTIONS', 'POST'])
def api_update_worldobj_image(worldobj_id):
    # Фронтальная часть приложения перед отправлением запроса на изменение изображения привязанного к элементу
    # отправляет OPTIONS запрос, на который необходимо ответить ответом с необходимыми заголовками, в котором
    # указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение объекта мира по запросу в базу данных
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    # Получение файла изображения из формы
    new = request.files["image"]
    # Сохранение названия файла
    filename = new.filename
    # Проверка на пустой файл
    if filename != '':
        # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
        if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
            # Удаление фотографии
            os.remove(worldobj.img_link[1:])
        # Создание уникального имени использую id объекта мира
        worldobj_img_name = "world" + str(worldobj.id) + ".jpg"
        # Сохранение изображения в папку под уникальным именем
        new.save(os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name))
        # Внесение изменений
        worldobj.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name)
    # Добавление измененного объекта мира в сессию изменений
    db.session.add(worldobj)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return jsonify({'message': 'World updated successfully'})


# Flask Функция для удаления фотографии объекта мира, идентификатор которого был указан. Изображение объекта
# мира будет удалено, если оно не являлось стандартным
@app.post('/worldobj/<int:worldobj_id>/delete_worldobj_image/')
def delete_worldobj_image(worldobj_id):
    # Получение объекта мира по запросу в базу данных
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(worldobj.img_link[1:])
        # Объекту мира присваивается стандартная фотография
        worldobj.img_link = "/staticFiles/images/QuestionMark.jpg"
        # Добавление измененного объекта мира в сессию изменений
        db.session.add(worldobj)
        # Фиксация изменений в БД
        db.session.commit()
    return redirect(url_for('world', world_id=worldobj.world_id))


# React Функция для удаления объекта мира, указанного по ее идентификатору, а также изображения, которое с ним связано
@app.route('/api/worldobj/<int:worldobj_id>/delete/', methods=('GET', 'OPTIONS', 'DELETE'))
def api_worldobj_delete(worldobj_id):
    # Фронтальная часть приложения перед отправлением запроса на удаление элемента отправляет OPTIONS запрос,
    # на который необходимо ответить ответом с необходимыми заголовками, в котором указаны разрешенные методы
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return jsonify({'message': 'Approved'}), 201
    # Получение объекта мира по запросу в базу данных
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(worldobj.img_link[1:])
    # Удаление объекта мира
    db.session.delete(worldobj)
    # Фиксация изменений в БД
    db.session.commit()
    # Отсылка сообщения
    return {'message': 'WorldObj deleted successfully'}


# Flask Функция для удаления объекта мира, указанного по ее идентификатору, а также изображения, которое с ним связано
@app.post('/worldobj/<int:worldobj_id>/delete/')
def worldobj_delete(worldobj_id):
    # Получение объекта мира по запросу в базу данных
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    world_id = worldobj.world_id
    # Проверка ссылки на изображение, для того чтобы не удалить стандартную фотографию
    if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
        # Удаление фотографии
        os.remove(worldobj.img_link[1:])
    # Удаление объекта мира
    db.session.delete(worldobj)
    # Фиксация изменений в БД
    db.session.commit()
    return redirect(url_for('world', world_id=world_id))
