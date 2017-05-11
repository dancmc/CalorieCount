from flask import request, jsonify, render_template, redirect, url_for
from functools import wraps
from config import *
import jwt, imghdr, time
from databasehelper import DBHelper


def api_requires_token(func):
    # need wraps otherwise decorator only works for one function
    @wraps(func)
    def check_auth(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                # Authorization header should be in format Bearer <token>
                auth_token = auth_header.split(" ")[1]
            except:
                auth_token=""

            if auth_token:
                try:
                    payload = jwt.decode(auth_token, SECRET_KEY, algorithms=['HS256'])
                    id = payload.get("id")
                except jwt.ExpiredSignatureError:
                    return jsonify({"success":False,"error":'Signature expired. Please log in again.'}), 401
                except jwt.InvalidTokenError:
                    return jsonify({"success":False,"error":'Invalid token. Please log in again.'}), 401

                db= DBHelper()
                result = db.user_exists(id)
                db.close_connection()

                if result:
                    return func(*args, requesting_id=id,**kwargs)
                else :
                    return jsonify({"success": False, "error": "No such user."}), 401

        return jsonify({"success": False, "error": "Unauthorized"}), 401
    return check_auth

def page_requires_token(func):
    # need wraps otherwise decorator only works for one function
    @wraps(func)
    def check_auth(*args, **kwargs):
        auth_header = request.form.get('Authorization')
        if auth_header:
            try:
                # Authorization header should be in format Bearer <token>
                auth_token = auth_header.split(" ")[1]
            except:
                auth_token=""

            if auth_token:
                try:
                    payload = jwt.decode(auth_token, SECRET_KEY, algorithms=['HS256'])
                    id = payload.get("id")
                except jwt.ExpiredSignatureError:
                    return render_template("error.html", error_code=401, error_message="Authorization token signature expired. Please log in again.")
                except jwt.InvalidTokenError:
                    return render_template("error.html", error_code=401,
                                           error_message="Invalid token. Please log in again.")

                db= DBHelper()
                result = db.user_exists(id)
                db.close_connection()

                if result:
                    return func(*args, requesting_id=id,**kwargs)
                else :
                    return render_template("error.html", error_code=401,
                                           error_message="No such user.")

        return render_template("error.html", error_code=401,
                                           error_message="Unauthorized.")
    return check_auth

def validate_image(file):
    # remember to return read cursor to start
    ext = imghdr.what("", file.read())
    file.seek(0)
    return ext.lower() if ext else None

def make_token(user_id):
    # TODO change expiry
    encoded = jwt.encode({'iss': 'dancmc.io',
                          'exp': int(time.time()) + 3600,
                          'id': user_id}, SECRET_KEY, algorithm='HS256')
    return encoded.decode()