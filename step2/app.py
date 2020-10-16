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
import time
import math

# Config setting
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/WhisperTalk"
salt = 'neltia'
now = str(datetime.now())
myHash = hashlib.sha512(str(now + salt).encode('utf-8')).hexdigest()
app.config['SECRET_KEY'] = myHash

mongo = PyMongo(app)


# Error Process
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
