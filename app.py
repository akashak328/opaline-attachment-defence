from flask import Flask, render_template, Response, redirect, request, session, abort, url_for
from flask_mail import Mail, Message
from flask import send_file
import mysql.connector
import hashlib
from random import randint
from urllib.request import urlopen
import docx
from docx import Document
from pdf2docx import parse
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
import textwrap
from spire.doc import *
from spire.doc.common import *
import warnings

app = Flask(__name__)
app.secret_key = 'opaline_secret_key'

# ── Email Configuration ────────────────────────────────────────────────────────
mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "rndittrichy@gmail.com",
    "MAIL_PASSWORD": "lyylfimewwddjwnk"
}
app.config.update(mail_settings)
mail = Mail(app)

# ── Database Connection ────────────────────────────────────────────────────────
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    charset="utf8",
    database="malicious_email"
)

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    act = request.args.get("act")
    if request.method == 'POST':
        uname = request.form['uname']
        pwd   = request.form['pass']
        cursor = mydb.cursor()
        cursor.execute(
            'SELECT * FROM admin WHERE username = %s AND password = %s',
            (uname, pwd)
        )
        account = cursor.fetchone()
        if account:
            session['username'] = uname
            return redirect(url_for('admin'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)


@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    act = request.args.get("act")
    if request.method == 'POST':
        name   = request.form['name']
        mobile = request.form['mobile']
        uname  = request.form['uname']
        pass1  = request.form['pass']
        mycursor = mydb.cursor()
        mycursor.execute("SELECT count(*) FROM register WHERE uname=%s", (uname,))
        cnt = mycursor.fetchone()[0]
        if cnt == 0:
            mycursor.execute("SELECT max(id)+1 FROM register")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid = 1
            sql = "INSERT INTO register(id, name, mobile, uname, pass) VALUES (%s, %s, %s, %s, %s)"
            val = (maxid, name, mobile, uname, pass1)
            mycursor.execute(sql, val)
            mydb.commit()
            msg = "success"
            return redirect(url_for('register', act='1'))
        else:
            msg = 'fail'
    return render_template('register.html', msg=msg, act=act)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# ── Send Alert Mail ────────────────────────────────────────────────────────────
def sendmail(usermail, mess1, maxid, n1):
    with app.app_context():
        msg = Message(
            subject="Mail Alert",
            sender=app.config["MAIL_USERNAME"],
            recipients=[usermail]
        )
        msg.body = mess1
        mail.send(msg)


if __name__ == '__main__':
    app.run(debug=True)
