from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
#from .database_setup import app, db, Food
from app import app, lm, oid
from .database_setup import db, Food
from .forms import LoginForm
from .models import User
from .scraper import *

@app.route('/')
@app.route('/index')
#@login_required
def index():
    user = g.user
    posts = [
        { 
            'author': {'nickname': 'John'}, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': {'nickname': 'Susan'}, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template('index.html')
@app.route('/app')
@login_required
def view_app():
    return render_template('app.html')
@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect('/app', code=302)
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html', form=form,
                           providers=app.config['OPENID_PROVIDERS'])

@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html',
                           user=user,
                           posts=posts)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id)) 

@app.before_request
def before_request():
    g.user = current_user    

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))    
    

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect('/app', code=302)

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        #db.session.add(g.user)
        #db.session.commit()
        print('myasss')

from .forms import LoginForm, EditForm

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.fave_foods = form.fave_foods.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.fave_foods.data = g.user.fave_foods
    return render_template('edit.html', form=form)


