from flask import request, jsonify
from functools import wraps
from config import *
import jwt, imghdr
from databasehelper import DBHelper


def requires_token(func):

    def check_auth(requested_id, *args, **kwargs):
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
                    return func(requested_id, id, *args, **kwargs)
                else :
                    return jsonify({"success": False, "error": "No such user."}), 401

        return jsonify({"success": False, "error": "Unauthorized"}), 401
    return check_auth


def validate_image(file):
    # remember to return read cursor to start
    ext = imghdr.what("", file.read())
    file.seek(0)
    # ext = None if ext is None else ext.lower()
    return ext