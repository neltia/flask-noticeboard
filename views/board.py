# public
from public_lib import *
# flask
from config import app
from flask import Blueprint
# process
from pymongo import MongoClient
from flask import send_from_directory
from flask import jsonify
import math
# decorated_lib
from decorated_lib import login_required
# filter
from filters import format_datetime

# var setting
mongo = PyMongo(app)
blueprint = Blueprint("board", __name__, url_prefix='/board')
connection = MongoClient()

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# board
@blueprint.route("/list")
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

    tot_count = len(list(board.find({})))
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
        keyword=keyword,
        tot_count=tot_count
    )


@blueprint.route("/view/<idx>")
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
                "writer_id": data.get("writer_id", ""),
                "attachfile": data.get("attachfile", "")
            }
            comment = mongo.db.wt_comment
            comments = comment.find({"root_idx": str(data.get("_id"))})
            return render_template("view.html", result=result, comments=comments)
    return abort(404)


@blueprint.route("/write", methods=["GET", "POST"])
@login_required
def board_write():
    form = writeForm()
    if request.method == "POST":
        filename = None
        if "attachfile" in request.files:
            file = request.files["attachfile"]
            print(file)
            if file and allowed_file(file.filename, "file"):
                filename = check_filename(file.filename)
                file.save("./static/files/" + filename)

        writer_id = session.get("id")
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.values.get("content")
        print(name, title, contents)

        board = mongo.db.wt_board
        tot_count = len(list(board.find({})))
        cur_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.wt_board
        post = {
            "writer_id": writer_id,
            "num": tot_count + 1,
            "name": name,
            "title": title,
            "contents": contents,
            "date": cur_utc_time,
        }

        if filename is not None:
            post["attachfile"] = filename
        x = board.insert_one(post)
        return redirect(url_for("board_view", idx=x.inserted_id))
    else:
        return render_template("write.html", form=form, name=session["name"], tot_count=tot_count)


@blueprint.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):
    form = writeForm()
    if request.method == "GET":
        board = mongo.db.wt_board
        data = board.find_one({"_id": ObjectId(idx)})
        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("main_page"))
        else:
            if session.get("id") == data.get("writer_id"):
                return render_template("edit.html", form=form, data=data)
            else:
                flash("글 수정 권한이 없습니다.")
                return redirect(url_for("main_page"))
    else:
        title = request.form.get("title")
        contents = request.form.get("contents")
        board = mongo.db.board

        data = board.find_one({"_id": ObjectId(idx)})

        if data.get("writer_id") == session.get("id"):
            board.update_one({"_id": ObjectId(idx)}, {
                "$set": {
                    "title": title,
                    "contents": contents,
                }
            })
            flash("수정되었습니다.")
            return redirect(url_for("board_view", idx=idx))
        else:
            flash("글 수정 권한이 없습니다.")
            return redirect(url_for("main_page"))


@blueprint.route("/delete/<idx>")
def board_delete(idx):
    board = mongo.db.wt_board
    data = board.find_one({"_id": ObjectId(idx)})
    if data.get("writer_id") == session.get("id"):
        board.delete_one({"_id": ObjectId(idx)})
        flash("삭제되었습니다.")
    else:
        flash("글 삭제 권한이 없습니다.")
    return redirect(url_for("main_page"))


@blueprint.route("/upload_image", methods=["POST"])
def upload_image():
    if request.method == "POST":
        img_file = request.files["image"]
        print(img_file)
        if img_file and allowed_file(img_file.filename, "img"):
            filename = "{}_{}.jpg".format(str(int(datetime.now().timestamp()) * 1000), rand_generator())
            print(filename)
            savefilepath = os.path.join("./static/images", filename)
            print(savefilepath)
            img_file.save(savefilepath)
            return url_for("board_images", filename=filename)


@blueprint.route('/images/<filename>')
def board_images(filename):
    return send_from_directory('./static/images', filename)


@blueprint.route('/files/<filename>')
def board_files(filename):
    return send_file('./static/files/' + filename,
                    attachment_filename = filename,
                    as_attachment=True)


@blueprint.route("/comment_write", methods=["POST"])
def comment_write():
    try:
        print(session["id"])
    except:
        flash("회원가입 후 댓글을 달 수 있습니다.")
        return redirect(url_for("member_login"))

    if request.method == "POST":
        name = session.get("name")
        writer_id = session.get("id")
        root_idx = request.form.get("root_idx")
        ccomment = request.form.get("comment")
        current_utc_time = round(datetime.utcnow().timestamp() * 1000)

        comment = mongo.db.wt_comment

        post = {
            "root_idx": root_idx,
            "writer_id": writer_id,
            "name": name,
            "comment": ccomment,
            "date": current_utc_time,
        }

        print(post)
        comment.insert_one(post)
        return redirect(url_for("board_view", idx=root_idx))
    return abort(404)


@blueprint.route("/comment_delete/<idx>")
def comment_delete(idx):
    comment = mongo.db.wt_comment
    data = comment.find_one({"_id": ObjectId(idx)})
    if data.get("writer_id") == session.get("id"):
        comment.delete_one({"_id": ObjectId(idx)})
        flash("삭제되었습니다.")
    else:
        flash("댓글 삭제 권한이 없습니다.")
    return """<script>
        window.location = document.referrer;
        </script>"""
