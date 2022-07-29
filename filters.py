from config import app
from public_lib import *


# filter
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
