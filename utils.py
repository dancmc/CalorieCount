from flask import request, jsonify, render_template, redirect, url_for
from werkzeug.datastructures import FileStorage
import requests
from functools import wraps
from config import *
import jwt, imghdr, time, os, json, zlib, threading
from io import BytesIO, StringIO
from PIL import Image as im
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from Crypto.Cipher import ARC4, AES, DES
from base64 import urlsafe_b64encode, urlsafe_b64decode, b64encode
from databasehelper import DBHelper
from database import Image

db = DBHelper()


def response_error(message, error_code, website=False):
    print(website)
    return render_template("error.html", error_code=401, error_message=message) if website else jsonify(
        {"success": False, "error": message,"error_code":error_code}), 401


def decode_header(auth_header, key):
    if auth_header:
        try:
            # Authorization header should be in format Bearer <token>
            auth_token = auth_header.split(" ")
            auth_token = auth_token[1] if len(auth_token) >1 else auth_token[0]
        except:
            auth_token = ""

        if auth_token:
            try:
                payload = jwt.decode(auth_token, key, algorithms=['HS256'])
                return {"success": True, "payload": payload}
            except jwt.ExpiredSignatureError:
                return {"success": False, "error": 'Signature expired. Please log in again.', "error_code":1}
            except jwt.InvalidTokenError:
                return {"success": False, "error": 'Invalid token. Please log in again.', "error_code":2}
    else:
        return {"success": False, "error": 'No token or cookie sent.', "error_code":3}


def requires_token(func):
    # need wraps otherwise decorator only works for one function
    @wraps(func)
    def check_auth(*args, **kwargs):

        # auth header is for mobile
        auth_header = request.headers.get('Authorization')

        # csrf token/cookie for web
        cookie = request.cookies.get("user_token")
        header_csrf_token = request.headers.get('X-CSRF-TOKEN')
        form_csrf_token = request.form.get('X-CSRF-TOKEN')

        # ajax requests should receive JSON response too, and they send headers rather than form tokens
        # only non ajax form POSTs should receive html
        return_webpage = bool(cookie and form_csrf_token)

        # means originating from mobile device/server
        if auth_header:
            result = decode_header(auth_header, USER_TOKEN_SECRET)
            if not result.get("success"):
                return response_error(result.get("error"), result.get("error_code"), return_webpage)
            else:
                payload = result.get("payload")
                id = payload.get("user_id")
                if not payload.get("api_key"):
                    return response_error("No API key in token.", 4, return_webpage)
                elif not id:
                    return response_error("No valid user ID in csrf or auth token.", 5, return_webpage)
                elif not db.user_exists(id):
                    return response_error("No such user found.",6, return_webpage)
                else:
                    return func(*args, requesting_id=id, **kwargs)

        # means from website/ajax
        else:

            decode_result = decode_header(cookie, USER_TOKEN_SECRET)
            if decode_result.get("success"):
                payload = decode_result.get("payload")
                cookie_id = payload.get("user_id")
            else:
                return response_error(decode_result.get("error"), decode_result.get("error_code"))

            # check if cookie decoded correctly
            if not cookie_id:
                return response_error("No valid user ID in cookie.", 7, return_webpage)
            elif not db.user_exists(cookie_id):
                return response_error("No such user found.", 6, return_webpage)
            # check if csrf token in header decoded correctly
            else:

                result = decode_header(header_csrf_token, CSRF_TOKEN_SECRET) if header_csrf_token else decode_header(form_csrf_token,
                                                                                                         CSRF_TOKEN_SECRET)
                if not result or not result.get("success"):
                    return response_error(result.get("error"), result.get("error_code"),return_webpage)
                else:
                    payload = result.get("payload")
                    csrf_id = payload.get("user_id")

                    # don't hit db again
                    if not csrf_id:
                        return response_error("No valid user ID in csrf or auth token.", 5, return_webpage)
                    elif csrf_id != cookie_id:
                        return response_error("Cookie and token user IDs do not match.", 8, return_webpage)
                    else:
                        return func(*args, requesting_id=cookie_id, **kwargs)

    return check_auth


def validate_image(file):
    # remember to return read cursor to start
    ext = imghdr.what("", file.read())
    file.seek(0)
    return ext.lower() if ext else None


def save_image(folder, file, ext, filename=None):

    file.filename = filename if filename else random_b64_string(32) + "." + ext

    image = im.open(file)
    image_width = image.width
    image_height = image.height
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    image_path = folder + "/" + file.filename
    file.save(image_path)

    return {"image_width": image_width, "image_height": image_height, "image_size": file_size,
            "filename": file.filename}


def make_user_token(extras):
    # TODO change expiry
    base_dict = {'iss': 'dancmc.io', 'exp': int(time.time()) + USER_TOKEN_EXPIRY}
    base_dict.update(extras)
    encoded = jwt.encode(base_dict, USER_TOKEN_SECRET, algorithm='HS256')
    return encoded.decode()


def make_csrf_token(extras):
    # TODO change expiry
    base_dict = {'iss': 'dancmc.io', 'exp': int(time.time()) + USER_TOKEN_EXPIRY}
    base_dict.update(extras)
    encoded = jwt.encode(base_dict, CSRF_TOKEN_SECRET, algorithm='HS256')
    return encoded.decode()


def validate_postive_int(num, accept_none=False):
    if num is None:
        return accept_none
    if isinstance(num, int):
        pass
    else:
        try:
            num = float(num)
            if num % 1 != 0:
                return False
        except ValueError:
            return False
    return num > 0


def validate_positive_ints(*args, accept_none=False):
    for arg in args:
        if not validate_postive_int(arg, accept_none):
            return False
    return True


def validate_boolean(b, accept_none=False):
    if b is None:
        return accept_none
    if isinstance(b, bool):
        return b
    if isinstance(b, str):
        if b.lower() == "true":
            return True
        elif b.lower() == "false":
            return False
    return False


def encrypt_dict_aes(key, data):
    # key should be generated using Fernet.generate_key
    cipher = Fernet(key)

    # dict > string > bytes > enc bytes > b64 bytes > b64 string
    bites = bytes(json.dumps(data), "utf-8")
    encrypted = cipher.encrypt(bites)

    return urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_dict_aes(key, string):
    cipher = Fernet(key)

    # b64 string > b64 bytes > enc bytes > bytes > string > dict
    encrypted = urlsafe_b64decode(bytes(string, "utf-8"))
    bites = cipher.decrypt(encrypted)

    return json.loads(bites.decode("utf-8"))


def encrypt_dict_des(key, jsondict):

    # dict > string > enc bytes > b64 bytes > b64 string
    # 8 byte key
    des = DES.new(key)
    encrypted = des.encrypt(pad_string(json.dumps(jsondict), 8))

    return urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_dict_des(key, string):
    des = DES.new(key)

    # b64 string > b64 bytes > enc bytes > string > dict
    encrypted = urlsafe_b64decode(bytes(string, "utf-8"))
    string = des.decrypt(encrypted)

    return json.loads(string.decode("utf-8"))


def pad_string(string, multiple):
    extra = 8 - len(string) % multiple
    return string + " " * extra if extra != 0 else string

def get_milli(years=None, months=None, weeks=None, days=None, hours=None, mins=None, secs=None, ms=None):
    total = 0
    total += years*31536000000 if years else 0
    total += months*2592000000 if months else 0
    total += weeks*604800000 if weeks else 0
    total += days*86400000 if days else 0
    total += hours*3600000 if hours else 0
    total += mins*60000 if mins else 0
    total += secs*1000 if secs else 0
    total += ms if ms else 0
    return total

def random_b64_string(byte_length=24):
    random_bytes = os.urandom(byte_length)
    return urlsafe_b64encode(random_bytes).decode("utf-8")

def download_image(url, filename, file_id=None, image_type=None):
    #TODO consider resizing before saving
    r = requests.get(url)
    image = FileStorage(stream=BytesIO(r.content))
    ext  = validate_image(image)
    result = save_image(PROFILE_IMAGE_FOLDER, image, ext, filename=filename)

    if file_id and ext:
        image_ob = Image(image_id=file_id, uploader_id=-1, image_type=image_type,
                           image_height=result.get("image_height"), image_width=result.get("image_width"),
                           image_size= result.get("image_size"))
        return image_ob
    else:
        return None


