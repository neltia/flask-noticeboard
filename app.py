# lib
from public_lib import *
from flask import send_from_directory
from string import digits, ascii_uppercase, ascii_lowercase
import random
import os
import re
# views
from views import board
from views import users

# app set
from config import app
# Config setting
ALLOWED_EXTENSIONS_img = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_EXTENSIONS_file = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
if not os.path.exists("./static/files"):
    os.mkdir("./static/files")


# check expression
def allowed_file(filename, types):
    if types == "img":
        return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS_img
    if types == "file":
        return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS_file


def check_filename(filename):
    reg = re.compile(r'[^A-Za-z0-9_.가-힝-]')
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
            print(filename)
            filename = str(reg.sub('', '_'.join(filename.split()))).strip('._')
    return filename


def rand_generator(length=8):
    chars = ascii_lowercase + ascii_uppercase + digits
    return ''.join(random.sample(chars, length))


# handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template("page_not.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("page_not.html"), 500


@app.route("/")
def main_redirect():
    return redirect(url_for("board.main_page"))


app.register_blueprint(board.blueprint)
app.register_blueprint(users.blueprint)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
