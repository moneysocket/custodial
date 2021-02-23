#!/usr/bin/env python3
# Copyright (c) 2021 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php

import time

from flask import Flask, render_template, request, redirect
from flask_login import login_required, current_user, login_user, logout_user

from moneysocket.wad.wad import Wad
from moneysocket.beacon.beacon import MoneysocketBeacon
from moneysocket.beacon.location.websocket import WebsocketLocation

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
# app rpcs
###############################################################################

def getaccountinfo_rpc():
    info = rpc.call(['getaccountinfo'])
    accounts = info['accounts']
    for account in accounts:
        account['wad'] = str(Wad.from_dict(account['wad']))
        account['cap'] = str(Wad.from_dict(account['cap']))
    return accounts

def getaccountreceipts_rpc(account):
    info = rpc.call(['getaccountreceipts', account])
    return info['receipts']

def connect_rpc(account, beacon):
    info = rpc.call(['connect', account, beacon])
    return info

def clear_rpc(account):
    info = rpc.call(['clear', account])
    return info

def rm_rpc(account):
    info = rpc.call(['rm', account])
    return info

def create_rpc(username):
    cap = config['Account']['Cap']
    start = config['Account']['StartBalance']
    info = rpc.call(['create', '-a', username, '-c', cap, start])
    return info

###############################################################################
# app actions
###############################################################################

def format_receipts(receipts):
    # make info easy to render into templete
    new = []
    for session in receipts:
        new_session = {'entries': []}
        for entry in session:
            new_entry = {'values': []}
            for k, v in entry.items():
                if k == 'type':
                    t = v.replace("_", " ").title()
                    new_entry['type'] = t
                elif k == 'time':
                    t = time.ctime(v)
                    new_entry['time'] = t
                elif k == 'wad':
                    w = Wad.from_dict(v)
                    new_entry['values'].append(('Wad', str(w)))
                else:
                    new_entry['values'].append((k.title(), str(v)))
            new_session['entries'].append(new_entry)
        new.append(new_session)
    return new

def list_receipts(account):
    receipts = getaccountreceipts_rpc(account)
    receipts = format_receipts(receipts)
    return render_template('receipts.html', account_name=account,
                           receipts=receipts, n_receipts=len(receipts))

def generate_beacon(account):
    beacon = MoneysocketBeacon()
    location = WebsocketLocation(config['Beacon']['RelayLocation'])
    beacon.add_location(location)
    info = connect_rpc(account, str(beacon))
    if not info['success']:
        return render_template("accounts.html", error=info['error'])
    accounts = getaccountinfo_rpc()
    return render_template("accounts.html", accounts=accounts)

def clear_beacons(account):
    info = clear_rpc(account)
    if not info['success']:
        return render_template("accounts.html", error=info['error'])
    accounts = getaccountinfo_rpc()
    return render_template("accounts.html", accounts=accounts)

def remove_account(account):
    info = clear_rpc(account)
    if not info['success']:
        return render_template("accounts.html", error=info['error'])
    info = rm_rpc(account)
    if not info['success']:
        return render_template("accounts.html", error=info['error'])
    accounts = getaccountinfo_rpc()
    return render_template("accounts.html", accounts=accounts)

def new_account(username):
    info = create_rpc(username)
    if not info['success']:
        return render_template("accounts.html", error=info['error'])
    accounts = getaccountinfo_rpc()
    return render_template("accounts.html", accounts=accounts)

###############################################################################
# app interaction
###############################################################################

@app.route('/accounts', methods = ['POST', 'GET'])
@login_required
def accounts():
    if request.method == 'POST':
        if 'list_receipts' in request.form:
            action = 'list_receipts'
            return list_receipts(request.form[action])
        elif 'generate_beacon' in request.form:
            action = 'generate_beacon'
            return generate_beacon(request.form[action])
        elif 'clear_beacons' in request.form:
            action = 'clear_beacons'
            return clear_beacons(request.form[action])
        elif 'remove_account' in request.form:
            action = 'remove_account'
            return remove_account(request.form[action])
        elif 'new_account' in request.form:
            # TODO cap max accounts per user
            action = 'new_account'
            return new_account(request.form[action])
        else:
            return render_template("accounts.html", error="unknown action")
    else:
        # TODO filter by db ownership
        accounts = getaccountinfo_rpc()
        return render_template('accounts.html', accounts=accounts)

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
    return render_template('login.html', account_cap=config['Account']['Cap'])


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
    app.run(host=host, port=port, debug=True)
