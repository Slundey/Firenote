import functools
import os
from . import db
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from textwrap import wrap
from firenote.db import get_db

# import os

# from flask import Flask,render_template,request
# from . import db, auth

def wrap_filenames(name: str, width: int = 12):
    return "\n".join(wrap(name, width))


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

    # a simple page that says hello
    @app.route('/')
    def hello():
        return redirect(url_for('auth.login'))

    @app.route('/editor')
    def editor():
        return render_template("editor.html")

    @app.route("/library")
    def library():
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
                        "INSERT INTO user (username, password) VALUES (?, ?)",
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
                'SELECT * FROM user WHERE username = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['user_id'] = user['id']
                return redirect(url_for('library'))

            flash(error)

        return render_template('auth/login.html')

        @bp.before_app_request
        def load_logged_in_user():
            user_id = session.get('user_id')

            if user_id is None:
                g.user = None
            else:
                g.user = get_db().execute(
                    'SELECT * FROM user WHERE id = ?', (user_id)
                ).fetchone()

        @bp.route('/logout')
        def logout():
            session.clear()
            return redirect(url_for('library'))

        def login_required(view):
            @functools.wraps(view)
            def wrapped_view(**kwargs):
                if g.user is None:
                    return redirect(url_for('auth.login'))

                return view(**kwargs)
            return wrapped_view

    db.init_app(app)
    app.register_blueprint(bp)

    return app
