import os

IMG_FORMATS = ("png", "jpg", "gif", "svg")

settings = {
    "port": 8888,
    "static_path": "/tmp",
    "phantomjs_path": "phantomjs",
    "render_script": os.getcwd() + "/render_one.coffee",
    "view_size": "1280x1024",
    "thumb_size": "320x200",
    "ua_string": "Thumbnail Bot 1.0",
    "image_format": "jpg",
}
