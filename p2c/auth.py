import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from p2c.db import get_db, query_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username'].lower() #make the usernames not case sensitive
        password = request.form['password']
        db = get_db()
        cur = db.cursor()
        error = None
        cur.execute(
            'SELECT id FROM users WHERE username = (%s)', (username,)
        )
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif cur.fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            cur.execute(
                'INSERT INTO users (username, password) VALUES ((%s), (%s))',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = query_db(
            'SELECT * FROM users WHERE username = (%s)', (username,), True
        )

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = query_db('SELECT * FROM users WHERE id = (%s)', (user_id,), True)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
