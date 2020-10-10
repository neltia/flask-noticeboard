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
import time
import math

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import DataRequired, Email

# Config setting
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/WhisperTalk"
salt = 'neltia'
now = str(datetime.now())
myHash = hashlib.sha512(str(now + salt).encode('utf-8')).hexdigest()
app.config['SECRET_KEY'] = myHash

mongo = PyMongo(app)


class ContactForm(FlaskForm):
    name = StringField("사용자 이름",  [DataRequired()])
    email = EmailField('이메일 주소', [DataRequired(), Email()])
    pw = PasswordField("비밀번호",  [DataRequired()])
    code = StringField('인증코드', [DataRequired()])


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
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


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
def board_write():
    if request.method == "POST":
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")
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
    else:
        return render_template("write.html")


@app.route("/register", methods=["GET", "POST"])
def member_new():
    if request.method == "POST":
        name = request.form.get("name", type=str)
        email = request.form.get("email", type=str)
        pass1 = request.form.get("pass", type=str)
        pass2 = request.form.get("pass2", type=str)
        
        if pass1 != pass2:
            flash("비밀번호가 일치하지 않습니다.")
            return render_template("register.html")
        
        cur_utc_time = round(datetime.utcnow().timestamp() * 1000)
        wt_members = mongo.db.wt_members
        post = {
            "name": name,
            "email": email,
            "pass": pass1,
            "registerdate": cur_utc_time,
            "logintime": "",
            "logincount": 0,
        }
        
        wt_members.insert_one(post)
        return redirect(url_for("member_login"))
    else:
        form = ContactForm()
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def member_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pass")

        members = mongo.db.members
        data = members.find_one({"email": email})

        if data is None:
            flash("회원정보가 없습니다.")
            return redirect(url_for("member_join"))
        else:
            if data.get("pass") == password:
                session["email"] = email
                session["name"] = data.get("name")
                session["id"] = str(data.get("_id"))
                session.permanent = True
                return redirect(url_for("lists"))
            else:
                flash("비밀번호가 일치하지 않습니다.")
                return redirect(url_for("member_login"))
    else:
        return render_template("login.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
