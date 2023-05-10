import os
import datetime
import sqlalchemy
from flask import Flask, render_template, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TIMESTAMP
from sqlalchemy import func
from werkzeug.utils import secure_filename

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join('staticFiles', 'images')

app = Flask(__name__, template_folder='templates', static_folder='staticFiles')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'sqlite_darts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'Secret key'


db = SQLAlchemy(app)


class LongRead(db.Model):
    __tablename__ = 'LongRead'
    id = db.Column(db.Integer, primary_key=True)
    world_id = db.Column(db.Integer, db.ForeignKey('World.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    img_link = db.Column(db.String(200), nullable=True)

    # from timeline
    map_link = db.Column(db.String(200), nullable=True)
    time_line_link = db.Column(db.String(200), nullable=True)

    chapters = db.relationship('Chapter', backref='longread', lazy=True)
    blockcontents = db.relationship('BlockContent', backref='longread', lazy=True)

    def __repr__(self):
        return f'<LongRead {self.name}>'


@app.route('/explore/')
def longread_index():
    longreads = LongRead.query.all()
    return render_template('longread_index.html', longreads=longreads)


@app.route('/longreads/<int:longread_id>/')
def longread(longread_id):
    longread = LongRead.query.get_or_404(longread_id)
    chapters = Chapter.query.filter(Chapter.longread_id == longread_id).all()
    return render_template('longread.html', longread=longread, chapters=chapters)


@app.route('/worlds/<int:world_id>/create/', methods=('GET', 'POST'))
def longread_create(world_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        longread = LongRead(world_id=world_id,
                            name=name,
                            description=description)

        db.session.add(longread)
        db.session.flush()
        db.session.refresh(longread)
        filename = uploaded_img.filename
        if filename == '':
            longread.img_link = "/staticFiles/images/QuestionMark.jpg"
        else:
            longread_img_name = "longread" + str(longread.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name))
            longread.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name)
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('create_longread.html', world_id=world_id)


@app.route('/longreads/<int:longread_id>/edit/', methods=('GET', 'POST'))
def longread_edit(longread_id):
    longread = LongRead.query.get_or_404(longread_id)
    longread_id = longread.id
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        filename = uploaded_img.filename
        if filename != '':
            if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
                os.remove(longread.img_link[1:])
            longread_img_name = "longread" + str(longread.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name))
            longread.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], longread_img_name)
        longread.name = name
        longread.description = description

        db.session.add(longread)
        db.session.commit()

        return redirect(url_for('longread', longread_id=longread_id))

    return render_template('edit_longread.html', longread=longread)


@app.post('/longreads/<int:longread_id>/delete_longread_image/')
def delete_longread_image(longread_id):
    longread = LongRead.query.get_or_404(longread_id)
    if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
        os.remove(longread.img_link[1:])
        longread.img_link = "/staticFiles/images/QuestionMark.jpg"
        db.session.add(longread)
        db.session.commit()
    return redirect(url_for('longread', longread_id=longread_id))


@app.post('/longreads/<int:longread_id>/delete/')
def longread_delete(longread_id):
    longread = LongRead.query.get_or_404(longread_id)
    world_id = longread.world_id
    chapters = Chapter.query.filter(Chapter.longread_id == longread_id).all()
    for chapter in chapters:
        chapter_delete(chapter.id)
    if longread.img_link != "/staticFiles/images/QuestionMark.jpg":
        os.remove(longread.img_link[1:])
    db.session.delete(longread)
    db.session.commit()
    return redirect(url_for('world', world_id=world_id))


class Chapter(db.Model):
    __tablename__ = 'Chapter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    longread_id = db.Column(db.Integer, db.ForeignKey('LongRead.id'), nullable=False)

    blockcontents = db.relationship('BlockContent', backref='chapter', lazy=True)

    def __repr__(self):
        return f'<Chapter {self.name}>'


@app.route('/chapter/<int:chapter_id>/')
def chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    blockcontents = BlockContent.query.filter(BlockContent.chapter_id == chapter_id,
                                              BlockContent.longread_id == chapter.longread_id).all()
    return render_template('chapter.html', chapter=chapter, blockcontents=blockcontents)


@app.route('/longreads/<int:longread_id>/create/', methods=('GET', 'POST'))
def chapter_create(longread_id):
    if request.method == 'POST':
        name = request.form['name']

        chapter = Chapter(name=name, longread_id=longread_id)

        db.session.add(chapter)
        db.session.commit()

        return redirect(url_for('longread', longread_id=longread_id))

    return render_template('create_chapter.html', longread_id=longread_id)


@app.route('/chapter/<int:chapter_id>/edit/', methods=('GET', 'POST'))
def chapter_edit(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    longread_id = chapter.longread_id
    if request.method == 'POST':
        name = request.form['name']

        chapter.name = name
        chapter.longread_id = longread_id

        db.session.add(chapter)
        db.session.commit()

        return redirect(url_for('chapter', chapter_id=chapter_id))

    return render_template('edit_chapter.html', chapter=chapter)


@app.post('/chapter/<int:chapter_id>/delete/')
def chapter_delete(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    longread_id = chapter.longread_id
    blockcontents = BlockContent.query.filter(BlockContent.chapter_id == chapter_id,
                                              BlockContent.longread_id == chapter.longread_id).all()
    for blockcontent in blockcontents:
        blockcontent_delete(blockcontent.id)
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for('longread', longread_id=longread_id))


class BlockContent(db.Model):
    __tablename__ = 'BlockContent'
    id = db.Column(db.Integer, primary_key=True)
    longread_id = db.Column(db.Integer, db.ForeignKey('LongRead.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('Chapter.id'), nullable=False)
    text = db.Column(db.String(10000), nullable=True)
    img_link = db.Column(db.String(200), nullable=True)

    # from event
    coordx = db.Column(db.Integer, nullable=True)
    coordy = db.Column(db.Integer, nullable=True)
    time = db.Column(db.DateTime(timezone=True), nullable=True)
    floating_text = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<BlockContent {self.name}>'


@app.route('/blockcontent/<int:longread_id>/<int:chapter_id>/create/', methods=('GET', 'POST'))
def blockcontent_create(longread_id, chapter_id):
    if request.method == 'POST':
        text = request.form['text']
        uploaded_img = request.files['uploaded-file']
        coordx = -1
        coordy = -1
        time = datetime.datetime.now()
        floating_text = ""

        blockcontent = BlockContent(longread_id=longread_id,
                                    chapter_id=chapter_id,
                                    text=text,
                                    coordx=coordx,
                                    coordy=coordy,
                                    time=time,
                                    floating_text=floating_text)
        db.session.add(blockcontent)
        db.session.flush()
        db.session.refresh(blockcontent)
        filename = uploaded_img.filename
        if filename == '':
            blockcontent.img_link = "/staticFiles/images/font.jpg"
        else:
            blockcontent_img_name = "blockcontent" + str(blockcontent.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name))
            blockcontent.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name)
        db.session.commit()
        return redirect(url_for('chapter', chapter_id=chapter_id))

    return render_template('create_blockcontent.html', chapter_id=chapter_id)


@app.route('/blockcontent/<int:blockcontent_id>/edit/', methods=('GET', 'POST'))
def blockcontent_edit(blockcontent_id):
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    chapter_id = blockcontent.chapter_id
    if request.method == 'POST':
        text = request.form['text']
        uploaded_img = request.files['uploaded-file']
        filename = uploaded_img.filename
        if filename != '':
            if blockcontent.img_link != "/staticFiles/images/font.jpg":
                os.remove(blockcontent.img_link[1:])
            blockcontent_img_name = "blockcontent" + str(blockcontent.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name))
            blockcontent.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], blockcontent_img_name)
        blockcontent.text = text

        db.session.add(blockcontent)
        db.session.commit()

        return redirect(url_for('chapter', chapter_id=chapter_id))

    return render_template('edit_blockcontent.html', blockcontent=blockcontent)


@app.post('/blockcontent/<int:blockcontent_id>/delete_blockcontent_image/')
def delete_blockcontent_image(blockcontent_id):
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    if blockcontent.img_link != "/staticFiles/images/font.jpg":
        os.remove(blockcontent.img_link[1:])
        blockcontent.img_link = "/staticFiles/images/font.jpg"
        db.session.add(blockcontent)
        db.session.commit()
    return redirect(url_for('chapter', chapter_id=blockcontent.chapter_id))


@app.post('/blockcontent/<int:blockcontent_id>/delete/')
def blockcontent_delete(blockcontent_id):
    blockcontent = BlockContent.query.get_or_404(blockcontent_id)
    chapter_id = blockcontent.chapter_id
    if blockcontent.img_link != "/staticFiles/images/font.jpg":
        os.remove(blockcontent.img_link[1:])
    db.session.delete(blockcontent)
    db.session.commit()
    return redirect(url_for('chapter', chapter_id=chapter_id))


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


@app.route('/')
def index():
    worlds = World.query.all()
    return render_template('world_index.html', worlds=worlds)

@app.route('/worlds/')
def world_index():
    worlds = World.query.all()
    return render_template('world_index.html', worlds=worlds)


@app.route('/worlds/<int:world_id>/')
def world(world_id):
    world = World.query.get_or_404(world_id)
    longreads = LongRead.query.filter(LongRead.world_id == world_id).all()
    worldobjs = WorldObj.query.filter(WorldObj.world_id == world_id).all()
    return render_template('world.html', world=world, longreads=longreads, worldobjs=worldobjs)


@app.route('/worlds/create/', methods=('GET', 'POST'))
def world_create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        world = World(name=name,
                      description=description)

        db.session.add(world)
        db.session.flush()
        db.session.refresh(world)
        filename = uploaded_img.filename
        if filename == '':
            world.img_link = "/staticFiles/images/QuestionMark.jpg"
        else:
            world_img_name = "world" + str(world.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], world_img_name))
            world.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], world_img_name)
        db.session.commit()
        return redirect(url_for('world_index'))

    return render_template('create_world.html')


@app.route('/worlds/<int:world_id>/edit/', methods=('GET', 'POST'))
def world_edit(world_id):
    world = World.query.get_or_404(world_id)
    world_id = world.id

    if request.method == 'POST':
        name = request.form['name']
        uploaded_img = request.files['uploaded-file']
        description = request.form['description']
        filename = uploaded_img.filename
        if filename != '':
            if world.img_link != "/staticFiles/images/QuestionMark.jpg":
                os.remove(world.img_link[1:])
            world_img_name = "world" + str(world.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], world_img_name))
            world.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], world_img_name)
        world.name = name
        world.description = description

        db.session.add(world)
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('edit_world.html', world=world)


@app.post('/worlds/<int:world_id>/delete_world_image/')
def delete_world_image(world_id):
    world = World.query.get_or_404(world_id)
    if world.img_link != "/staticFiles/images/QuestionMark.jpg":
        os.remove(world.img_link[1:])
        world.img_link = "/staticFiles/images/QuestionMark.jpg"
        db.session.add(world)
        db.session.commit()
    return redirect(url_for('world', world_id=world_id))


@app.post('/worlds/<int:world_id>/delete/')
def world_delete(world_id):
    world = World.query.get_or_404(world_id)
    longreads = LongRead.query.filter(LongRead.world_id == world_id).all()
    worldobjs = WorldObj.query.filter(WorldObj.world_id == world_id).all()
    for longread in longreads:
        longread_delete(longread.id)
    for worldobj in worldobjs:
        worldobj_delete(worldobj.id)
    if world.img_link != "/staticFiles/images/QuestionMark.jpg":
        os.remove(world.img_link[1:])
    db.session.delete(world)
    db.session.commit()
    return redirect(url_for('world_index'))


blockcontents = db.Table('blockcontents',
                         db.Column('blockcontent_id', db.Integer, db.ForeignKey('BlockContent.id'), primary_key=True),
                         db.Column('worldobj_id', db.Integer, db.ForeignKey('WorldObj.id'), primary_key=True)
                         )


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


@app.route('/worlds/<int:world_id>/create_worldobj/', methods=('GET', 'POST'))
def worldobj_create(world_id):
    if request.method == 'POST':
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']

        worldobj = WorldObj(world_id=world_id,
                            description=description)

        db.session.add(worldobj)
        db.session.flush()
        db.session.refresh(worldobj)
        filename = uploaded_img.filename
        if filename == '':
            worldobj.img_link = "/staticFiles/images/QuestionMark.jpg"
        else:
            worldobj_img_name = "worldobj" + str(worldobj.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name))
            worldobj.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name)
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('create_worldobj.html', world_id=world_id)


@app.route('/worldobj/<int:worldobj_id>/edit/', methods=('GET', 'POST'))
def worldobj_edit(worldobj_id):
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    world_id = worldobj.world_id
    if request.method == 'POST':
        description = request.form['description']
        uploaded_img = request.files['uploaded-file']
        filename = uploaded_img.filename
        if filename != '':
            if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
                os.remove(worldobj.img_link[1:])
            worldobj_img_name = "worldobj" + str(worldobj.id) + ".jpg"
            uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name))
            worldobj.img_link = "/" + os.path.join(app.config['UPLOAD_FOLDER'], worldobj_img_name)
        worldobj.description = description

        db.session.add(worldobj)
        db.session.commit()

        return redirect(url_for('world', world_id=world_id))

    return render_template('edit_worldobj.html', worldobj=worldobj)


@app.post('/worldobj/<int:worldobj_id>/delete_worldobj_image/')
def delete_worldobj_image(worldobj_id):
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
        os.remove(worldobj.img_link[1:])
        worldobj.img_link = "/staticFiles/images/QuestionMark.jpg"
        db.session.add(worldobj)
        db.session.commit()
    return redirect(url_for('world', world_id=worldobj.world_id))


@app.post('/worldobj/<int:worldobj_id>/delete/')
def worldobj_delete(worldobj_id):
    worldobj = WorldObj.query.get_or_404(worldobj_id)
    world_id = worldobj.world_id
    if worldobj.img_link != "/staticFiles/images/QuestionMark.jpg":
        os.remove(worldobj.img_link[1:])
    db.session.delete(worldobj)
    db.session.commit()
    return redirect(url_for('world', world_id=world_id))

