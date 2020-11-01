from flask import Flask
from flask import render_template
from flask import request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask import abort
from flask import redirect
from flask import url_for
import hashlib
from flask import flash
from flask import session
from functools import wraps
import time
import math

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms.widgets import TextArea
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

# Config setting
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/WhisperTalk"
salt = 'neltia'
now = str(datetime.now())
myHash = hashlib.sha512(str(now + salt).encode('utf-8')).hexdigest()
app.config['SECRET_KEY'] = myHash
mongo = PyMongo(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            return redirect(url_for("member_login", next_url=request.url))
        return f(*args, **kwargs)
    return decorated_function


class personForm(FlaskForm):
    name = StringField("사용자 이름", validators=[DataRequired()])
    email = EmailField('이메일 주소', validators=[DataRequired(), Email()])
    pw = PasswordField("비밀번호", validators=[DataRequired()])
    pw2 = PasswordField("비밀번호 확인", validators=[DataRequired()])


class writeForm(FlaskForm):
    title = StringField("제목", validators=[DataRequired()])
    content = StringField("내용", widget=TextArea())


@app.errorhandler(404)
def page_not_found(error):
    return render_template("page_not.html"), 404


@app.template_filter("formatdatetime")
def format_datetime(timestamp):
    if timestamp is None:
        return ""
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(
        now_timestamp
    )
    timestamp = datetime.fromtimestamp((int(timestamp) / 1000)) + offset
    return timestamp.strftime("%Y-%m-%d %H:%M")


@app.route("/")
@app.route("/list")
def main_page():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", "", type=str)

    query = {}
    search_list = []

    if search == 0:
        search_list.append({"title": {"$regex": keyword}})
    elif search == 1:
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 2:
        search_list.append({"title": {"$regex": keyword}})
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 3:
        search_list.append({"name": {"$regex": keyword}})

    if len(search_list) > 0:
        query = {"$or": search_list}

    board = mongo.db.wt_board
    datas = board.find(query).sort("date", -1).skip((page-1) * limit).limit(limit)

    tot_count = board.count_documents(query)
    last_page_num = math.ceil(tot_count / limit)

    block_size = 5
    block_num = int((page-1) / block_size)
    block_start = int((block_size * block_num) + 1)
    block_last = math.ceil(block_start + (block_size-1))

    return render_template(
        "index.html",
        lists=datas,
        limit=limit,
        page=page,
        block_start=block_start,
        block_last=block_last,
        last_page=last_page_num,
        search=search,
        keyword=keyword
    )


@app.route("/view/<idx>")
def board_view(idx):
    if idx is not None:
        board = mongo.db.wt_board
        data = board.find_one({"_id": ObjectId(idx)})
        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "date": data.get("date"),
                "view": data.get("view"),
            }
            return render_template("view.html", result=result)
    return abort(404)


@app.route("/write", methods=["GET", "POST"])
@login_required
def board_write():
    form = writeForm()
    if request.method == "POST":
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("content")
        print(name, title, contents)

        board = mongo.db.wt_board
        tot_count = board.count_documents({})
        cur_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.wt_board
        post = {
            "num": tot_count + 1,
            "name": name,
            "title": title,
            "contents": contents,
            "date": cur_utc_time,
            "view": 0,
        }
        x = board.insert_one(post)
        return redirect(url_for("board_view", idx=x.inserted_id))
    elif request.method == "GET":
        if session.get('logged_in'):
            return render_template("write.html", form=form, name=session["name"])
        else:
            flash("회원가입 후 작성할 수 있습니다.")
            return redirect(url_for("member_new"))
    else:
        abort(404)


@app.route("/register", methods=["GET", "POST"])
def member_new():
    form = personForm()
    if request.method == "POST":
        name = request.form.get("name", type=str)
        email = request.form.get("email", type=str)
        pass1 = request.form.get("pw", type=str)
        pass2 = request.form.get("pw2", type=str)

        if pass1 != pass2:
            flash("아이디나 비밀번호가 올바르지 않습니다.")
            return render_template("register.html", form=form)

        if(2 > len(name) or len(name) > 5):
            flash("아이디는 2 ~ 5자리 사이로 입력해주세요.")
            return render_template("register.html", form=form)
        
        if(len(pass1) < 8):
            flash("비밀번호는 8자리 이상으로 작성해주세요.")
            return render_template("register.html", form=form)

        cur_utc_time = round(datetime.utcnow().timestamp() * 1000)
        wt_members = mongo.db.wt_members
        post = {
            "name": name,
            "email": email,
            "pass": hashlib.sha512(pass1.encode()).hexdigest(),
            "registerdate": cur_utc_time,
            "logintime": "",
            "logincount": 0,
        }
        
        wt_members.insert_one(post)
        return redirect(url_for("member_login"))
    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def member_login():
    form = personForm()
    if request.method == "GET":
        next_url = request.args.get("next_url", type=str)
        if next_url is not None:
            return render_template("login.html", form=form, next_url=next_url)
        else:
            return render_template("login.html", form=form)
    elif request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pw")
        next_url = request.form.get("next_url", type=str)

        members = mongo.db.wt_members
        data = members.find_one({"email": email})

        if data is None:
            flash("회원정보가 없습니다.")
            return redirect(url_for("member_new"))
        else:
            if data.get("pass") == hashlib.sha512(password.encode()).hexdigest():
                session["email"] = email
                session["name"] = data.get("name")
                session["id"] = str(data.get("_id"))
                session['logged_in'] = True
                if next_url is not None:
                    return redirect(next_url)
                else:
                    return redirect(url_for("main_page"))
            else:
                flash("아이디나 비밀번호가 올바르지 않습니다.")
                return redirect(url_for("member_login"))
    else:
        return render_template("login.html", form=form)


@app.route("/profile/<mail>")
def member_profile(mail):
    if request.method == "GET":
        if session.get('logged_in'):
            mail = session["email"].split("@")[0]
            return render_template("profile.html", mail=mail)
        else:
            flash("정보를 볼 권한이 없습니다.")
            return redirect(url_for("main_page"))


@app.route("/logout", methods=["GET", "POST"])
def member_logout():
    del session["name"]
    del session["id"]
    del session["email"]
    session['logged_in'] = False
    return redirect(url_for("member_login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
