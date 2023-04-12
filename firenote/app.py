import functools
import os
import db
from flask import (
    Flask, Blueprint, current_app, flash, g, redirect, render_template, request, send_file, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from textwrap import wrap
from db import get_db
from secrets import token_urlsafe
import hashlib
import time
from datetime import timedelta
from fpdf import FPDF
import tempfile
import markdown
from bs4 import BeautifulSoup as bs


def sentinel():
    if not "username" in session:
        return redirect(url_for("auth.login"))
    else:
        return None


def gen_note_id(username) -> str:
    t = str(int(time.time()))
    s = bytearray(str(username) + t + token_urlsafe(8), encoding="utf-8")
    hobj = hashlib.sha256(s)
    return hobj.hexdigest()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'firenote.sqlite')
    )

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=60)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    bp = Blueprint('auth', __name__, url_prefix='/auth')

    @app.route('/')
    def index():
        if (x := sentinel()) is not None:
            return x
        return redirect(url_for('library'))

    # no file
    @app.route('/editor')
    def editor():
        if (x := sentinel()) is not None:
            return x
        id = gen_note_id(session["username"])
        # unlikely
        while len(get_db().execute("SELECT * FROM notes WHERE id=?", (id,)).fetchall()) > 0:
            id = gen_note_id(session["username"])
        config = [{"theme": session['theme'], "fontsize": session['fontsize']}]

        return render_template("editor.html", content=None, id=id, config=config)

    # file
    @app.route("/editor/<id>")
    def editor_specific(id):
        if (x := sentinel()) is not None:
            return x
        row = get_db().execute("SELECT * FROM notes WHERE id=? AND user=?",
                               (id, session["username"])).fetchone()
        config = [{"theme": session['theme'], "fontsize": session['fontsize']}]
        return render_template("editor.html", id=id, content=row[3], title=row[1], config=config)

    @app.post("/create")
    def create_note():
        id = gen_note_id(session['username'])
        title = request.form.get('title')
        description = request.form.get('description')
        genre = request.form.get('genres')
        get_db().execute("INSERT OR REPLACE INTO notes(id, title, description, content, user) VALUES(?, ?, ?, ?, ?)",
                         (id, title, description, "", session['username']))
        get_db().execute("INSERT OR REPLACE INTO notes_genres (note_id, genre_id) VALUES (?, ?)", (id, genre))
        get_db().commit()
        return id

    @app.post("/save")
    def save_file():
        content = request.form.get("content")
        id = request.form.get("id")

        # generate a new id because the file being saved is not present in db / you silly
        if id is None:
            id = gen_note_id(session["username"])
            # unlikely
            while len(get_db().execute("SELECT * FROM notes WHERE id=?", (id,)).fetchall()) > 0:
                id = gen_note_id(session["username"])
        get_db().execute("UPDATE notes SET content = ? WHERE id = ?",
                         (content, id))
        get_db().commit()
        return id

    @app.post("/edit")
    def edit_note():
        id = request.form.get('id')
        title = request.form.get('title')
        description = request.form.get('description')
        
        genre = request.form.get('genre')
        get_db().execute("UPDATE notes SET title = ?, description = ? WHERE id = ?",
                         (title, description, id))
        get_db().execute("UPDATE notes_genres SET genre_id = ? WHERE note_id = ?",
                         (genre, id))
        get_db().commit()
        return "edit success!"
    
    @app.post("/apply")
    def apply_settings():
        theme = request.form.get('theme')
        fontsize = request.form.get('fontsize')
        session['theme'] = theme
        session['fontsize'] = fontsize
        get_db().execute("UPDATE config SET darktheme = ?, fontsize = ? WHERE user = ?",
                         (theme, fontsize, session['username']))
        get_db().commit()
        return "settings applied!"
    
    @app.post("/sort")
    def sort_notes():
        genre = request.form.get("genre_id")
        session['sortby'] = genre
        return "reload"

    @app.route('/export', methods=['POST', 'GET'])
    def export_file():
        id = request.args.get('id')
        format = request.args.get('format')
        print(id)
        db = get_db()
        rows = db.execute(
            "SELECT title, content FROM notes WHERE id=? AND user=?", (
                id, session['username'],)
        ).fetchone()
        title, content = rows[0], rows[1]
        tmp = tempfile.TemporaryFile()

        match format:
            case "md":
                tmp.write(content.encode())
            case "pdf":
                pdf = FPDF()
                pdf.add_page()
                pdf.write_html(markdown.markdown(content))
                pdf.output(tmp)
            case "html":
                tmp.write(markdown.markdown(content).encode())
            case "txt":
                soup = bs(markdown.markdown(content))
                tmp.write(soup.get_text().encode())
            case _:
                ...
                # catch invalid format, unlikely case

        tmp.seek(0)
        return send_file(tmp, as_attachment=True, download_name=title + "." + format)

    @app.post("/delete/<id>")
    def delete(id):
        print(id)
        get_db().execute("DELETE FROM notes WHERE id=? AND user=?",
                         (id, session["username"]))
        get_db().execute("DELETE FROM notes_genres WHERE note_id=?",
                         (id,))
        get_db().commit()
        return "chiefin dat hoe"

    @app.route("/library")
    def library():
        if (x := sentinel()) is not None:
            return x

        noterows = get_db().execute(
            "SELECT id, title, description, notes_genres.genre_id FROM notes JOIN notes_genres ON notes.id = notes_genres.note_id WHERE notes.user = ? ORDER BY (notes_genres.genre_id = ?) DESC, notes_genres.genre_id ASC;", (session["username"], session.get('sortby')))
        genrerows = get_db().execute(
            "SELECT * FROM genres;"
        )

        notes = [{"id": row[0], "name": row[1], "description":row[2], "genre_id":row[3]} for row in noterows]
        genres = [{"id": row[0], "name": row[1]} for row in genrerows]
        config = [{"theme": session['theme'], "fontsize": session['fontsize']}]
        return render_template("library.html", notes=notes, config=config, genres=genres)
    

    @bp.route('/register', methods=('GET', "POST"))
    def register():

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            db = get_db()
            error = None

            if not username:
                error = 'Username required!'
            elif not password:
                error = 'Password required!'

            if error is None:
                try:
                    db.execute(
                        "INSERT INTO users (username, password) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
                    db.execute(
                        "INSERT INTO config (user) VALUES (?);",
                        (username,),
                    )
                    db.commit()

                except db.IntegrityError:
                    error = f"User {username} is already registered."
                else:
                    return redirect(url_for("auth.login"))

            flash(error)

        return render_template('auth/register.html')

    @bp.route('/login', methods=('GET', 'POST'))
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            db = get_db()
            error = None
            user = db.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['username'] = user['username']
                config = db.execute(
                    'SELECT * FROM config WHERE user = ?', (username,)
                ).fetchone()
                session['theme'] = config['darktheme']
                session['fontsize'] = config['fontsize']
                session['sortby'] = 1
                return redirect(url_for('library'))

            flash(error)

        return render_template('auth/login.html')

    @bp.before_app_request
    def load_logged_in_user():
        username = session.get('username')

        if username is None:
            g.user = None
        else:
            g.user = get_db().execute(
                'SELECT * FROM users WHERE username=?', (username,)
            ).fetchone()

    @bp.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('auth.login'))

    def login_required(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for('auth.login'))

            return view(**kwargs)

    db.init_app(app)
    app.register_blueprint(bp)

    return app
