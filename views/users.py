# public
from public_lib import *
# flask
from flask import Blueprint
# process
from pymongo import MongoClient

# var setting
blueprint = Blueprint("users", __name__, url_prefix='/users')
connection = MongoClient()

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@blueprint.route("/register", methods=["GET", "POST"])
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

        if(2 > len(name) or len(name) > 6):
            flash("아이디는 2 ~ 6자리 사이로 입력해주세요.")
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
            "registerdate": cur_utc_time
        }

        wt_members.insert_one(post)
        return redirect(url_for("member_login"))
    else:
        return render_template("register.html", form=form)


@blueprint.route("/login", methods=["GET", "POST"])
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


@blueprint.route("/profile/<mail>")
def member_profile(mail):
    if request.method == "GET":
        if session.get('logged_in'):
            mail = session["email"].split("@")[0]
            board = mongo.db.wt_board
            datas = board.find({"name": session["name"]}).sort("date", -1)
            return render_template("profile.html", mail=mail, datas=datas)
        else:
            flash("정보를 볼 권한이 없습니다.")
            return redirect(url_for("main_page"))


@blueprint.route("/logout", methods=["GET", "POST"])
def member_logout():
    del session["name"]
    del session["id"]
    del session["email"]
    session['logged_in'] = False
    return redirect(url_for("member_login"))
