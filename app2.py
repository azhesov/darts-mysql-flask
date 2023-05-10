import os

from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'sqlite_darts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    bio = db.Column(db.Text)

    def __repr__(self):
        return f'<Student {self.firstname}>'

class LongRead(db.Model):
    __tablename__ = 'LongRead'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    img_link = db.Column(db.String(200), nullable=False)
    text = db.Column(db.String(10000), nullable=False)

    def __repr__(self):
        return f'<LongRead {self.name}>'


@app.route('/')
def index():
    longreads = LongRead.query.all()
    return render_template('longread_index.html', longreads=longreads)


@app.route('/<int:longread_id>/')
def longread(longread_id):
    longread = LongRead.query.get_or_404(longread_id)
    return render_template('longread.html', longread=longread)


@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        img_link = request.form['img_link']
        text = request.form['text']
        longread = LongRead(name=name,
                          description=description,
                          img_link=img_link,
                          text=text)
        db.session.add(longread)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('create_longread.html')


@app.route('/<int:longread_id>/edit/', methods=('GET', 'POST'))
def edit(longread_id):
    longread = LongRead.query.get_or_404(longread_id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        img_link = request.form['img_link']
        text = request.form['text']

        longread.name = name
        longread.description = description
        longread.img_link = img_link
        longread.text = text

        db.session.add(longread)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('edit_longread.html', longread=longread)


@app.post('/<int:longread_id>/delete/')
def delete(longread_id):
    longread = LongRead.query.get_or_404(longread_id)
    db.session.delete(longread)
    db.session.commit()
    return redirect(url_for('index'))
