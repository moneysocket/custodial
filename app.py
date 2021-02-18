#!/usr/bin/env python3
# Copyright (c) 2021 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php

from flask import Flask, render_template, request, redirect
from flask_login import login_required, current_user, login_user, logout_user
from models import UserModel, db, login
from config import read_config
from terminus_rpc import TerminusRpc

###############################################################################
# read config file
###############################################################################

config = read_config()

###############################################################################
# rpc connection
###############################################################################

rpc = TerminusRpc(config)

###############################################################################
# setup flask and db
###############################################################################

app = Flask(__name__)
app.secret_key = config['Db']['SecretKey']
app.config['SQLALCHEMY_DATABASE_URI'] = ("sqlite:////" +
                                         config['Db']['DatabaseFile'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login.init_app(app)
login.login_view = 'login'
db.init_app(app)

###############################################################################
# database initialization
###############################################################################

@app.before_first_request
def create_table():
    print("create table")
    db.create_all()

###############################################################################
# app interaction
###############################################################################

@app.route('/accounts')
@login_required
def accounts():
    accounts_text = rpc.call(['getaccountinfo'])

    print(accounts_text)
    return render_template('accounts.html', getinfo_text=accounts_text)

@app.route('/')
def root():
    if current_user.is_authenticated:
        return redirect('/accounts')
    else:
        return redirect('/login')

###############################################################################
# login lifecycle
###############################################################################

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/accounts')
    if request.method == 'POST':
        email = request.form['email']
        user = UserModel.query.filter_by(email = email).first()
        if user is not None and user.check_password(request.form['password']):
            login_user(user)
            return redirect('/accounts')
    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect('/accounts')
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if UserModel.query.filter_by(email=email).first():
            return ('Email already present')
        user = UserModel(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/accounts')

###############################################################################
# run app server
###############################################################################

if __name__ == "__main__":
    # TODO use gunicorn and nginx
    host = config['Server']['Host']
    port = int(config['Server']['Port'])
    app.run(host=host, port=port)
