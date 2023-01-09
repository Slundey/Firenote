import functools
import os
import db
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from textwrap import wrap
from db import get_db

def wrap_filenames(name: str, width: int = 12):
    return "\n".join(wrap(name, width))

#implemented auth check, but not applied to all cases!
def sentinel():
    if not "uid" in session:
        return redirect(url_for("auth.login"))
    else: return None

def convertTuple(tup):
        # initialize an empty string
    str = ''
    for item in tup:
        str = str + item
    return str


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'firenote.sqlite')
    )

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
        if (x := sentinel()) is not None: return x
        return redirect(url_for('library'))

    # no file
    @app.route('/editor')
    def editor():
        if (x := sentinel()) is not None: return x
        return render_template("editor.html", content=None)

    # file
    @app.route("/editor/<id>")
    def editor_specific(id):
        if (x := sentinel()) is not None: return x
        return render_template("editor.html")

    @app.post("/save")
    def save_file():
        con = get_db()
        con.execute("INSERT INTO note")
        return ""



    @app.route("/library")
    def library():
        if (x := sentinel()) is not None: return x
        from secrets import token_urlsafe
        notes = [{"name": token_urlsafe(
            8), "id": token_urlsafe(32)} for _ in range(100)]
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
                session['uid'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('library'))

            flash(error)

        return render_template('auth/login.html')

    @bp.before_app_request
    def load_logged_in_user():
        user_id = session.get('uid')
        #name = session.get('username')

        if user_id is None:
            g.user = None
        else:
            g.user = get_db().execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone
           #g.user = get_db().execute(
            #    'SELECT id FROM users WHERE username = ?', (name,)
            #).fetchone()[0]

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
