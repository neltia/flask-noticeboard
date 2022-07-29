# flask
from flask import Flask
from flask import render_template
from flask import session
from flask import url_for
from flask import abort
from flask import redirect
from flask import request
from flask import send_file
from flask import flash

# flask wtforms
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms.widgets import TextArea
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

# db
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import hashlib

# data processing
import time
from datetime import datetime
import logging


class personForm(FlaskForm):
    name = StringField("사용자 이름", validators=[DataRequired()])
    email = EmailField('이메일 주소', validators=[DataRequired(), Email()])
    pw = PasswordField("비밀번호", validators=[DataRequired()])
    pw2 = PasswordField("비밀번호 확인", validators=[DataRequired()])


class writeForm(FlaskForm):
    title = StringField("제목", validators=[DataRequired()])
    content = StringField("내용", widget=TextArea())
