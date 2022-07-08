from flask import Flask
from public_lib import *
import hashlib

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/WhisperTalk"
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024
salt = 'neltia'
now = str(datetime.now())
ALLOWED_EXTENSIONS_img = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_EXTENSIONS_file = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
myHash = hashlib.sha512(str(now + salt).encode('utf-8')).hexdigest()
app.config['SECRET_KEY'] = myHash
