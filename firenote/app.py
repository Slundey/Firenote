from fileinput import filename
import functools
from io import BytesIO
import os
import db
from flask import (
    Flask, Blueprint, current_app, flash, g, redirect, render_template, request, send_file, send_from_directory, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from textwrap import wrap
from db import get_db
import json
from secrets import token_urlsafe
import hashlib, time
from datetime import timedelta
from fpdf import FPDF
from pathlib import Path


def wrap_filenames(name: str, width: int = 12):
    return "\n".join(wrap(name, width))

def sentinel():
    if not "username" in session:
        return redirect(url_for("auth.login"))
    else: return None

def gen_note_id(username) -> str:
    t = str(int(time.time()))
    s = bytearray(str(username) + t + token_urlsafe(8), encoding="utf-8")
    hobj = hashlib.sha256(s)
    return hobj.hexdigest()

def create_app(test_config=None):
    UPLOAD_FOLDER = '/uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'md', 'html'}

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        UPLOAD_FOLDER = UPLOAD_FOLDER,
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'firenote.sqlite')
    )

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes = 60)

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
        print(app.config['UPLOAD_FOLDER'])
        if (x := sentinel()) is not None: return x
        return redirect(url_for('library'))

    # no file
    @app.route('/editor')
    def editor():
        if (x := sentinel()) is not None: return x
        id = gen_note_id(session["username"])
            # unlikely
        while len(get_db().execute("SELECT * FROM notes WHERE id=?", (id,)).fetchall()) > 0:
            id = gen_note_id(session["username"])
        return render_template("editor.html", content=None, id=id)

    # file
    @app.route("/editor/<id>")
    def editor_specific(id):
        if (x := sentinel()) is not None: return x
        row = get_db().execute("SELECT * FROM notes WHERE id=? AND user=?", (id, session["username"])).fetchone()
        return render_template("editor.html", id=id, content=row[2], title=row[1])

    @app.post("/save")
    def save_file():
        content = request.form.get("content")
        id = request.form.get("id")
        if content is None: return json.dumps({"status": "bruh"})
        
        # generate a new id because the file being saved is not present in db / you silly
        if id is None:
            id = gen_note_id(session["username"])
            # unlikely
            while len(get_db().execute("SELECT * FROM notes WHERE id=?", (id,)).fetchall()) > 0:
                id = gen_note_id(session["username"])
        get_db().execute("INSERT OR REPLACE INTO notes(id, content, title, user, dir) VALUES(?, ?, ?, ?, ?)", (id, content, id, session["username"], "DEFAULT"))
        get_db().commit()
        return id

    import tempfile, markdown
    from bs4 import BeautifulSoup as bs

    @app.route('/export', methods = ['POST', 'GET'])
    def export_file():
        id = request.args.get('id')
        format = request.args.get('format')
        print(id)
        db = get_db()
        rows = db.execute(
            "SELECT title, content FROM notes WHERE id=? AND user=?", (id, session['username'],)
            ).fetchone()
        print(rows)
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
                # catch invalid format
                
        tmp.seek(0)
        return send_file(tmp, as_attachment=True, download_name=title + "." + format)
    
    @app.post("/delete/<id>")
    def delete(id):
        print(id)
        get_db().execute("DELETE FROM notes WHERE id=? AND user=?", (id, session["username"]))
        get_db().commit()
        return "chiefin dat hoe"
    
    @app.post("/rename")
    def rename():
        id = request.form.get("id")
        name = request.form.get("name")
        if name is None or id is None: return "nah"
        get_db().execute("UPDATE notes SET title=? WHERE id=? AND user=?", (name, id, session["username"]))
        get_db().commit()
        return "top g"

    @app.route("/library")
    def library():
        if (x := sentinel()) is not None: return x

        rows = get_db().execute("SELECT id, title FROM notes WHERE user=?", (session["username"],))
        notes = [{"id": row[0], "name": row[1]} for row in rows]
        return render_template("library.html", notes=notes)



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
            if g.user is None: return redirect(url_for('auth.login'))

            return view(**kwargs)

    db.init_app(app)
    app.register_blueprint(bp)

    return app
