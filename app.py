from flask import Flask, url_for, render_template, request, redirect, jsonify, make_response, json, send_from_directory, Response
import requests, os
import jwt, time, uuid
from PIL import Image
from werkzeug.utils import secure_filename
from whatsappclient import WhatsappInstance
from databasehelper import DBHelper
from config import *
from utils import *
from flask_cors import CORS
from authomatic import Authomatic
from authomatic.adapters import WerkzeugAdapter
from d_oauth.auth import Auth
from d_oauth.user import User


app = Flask(__name__)
CORS(app)
db = DBHelper()


# listen for third party clients
# WhatsappInstance().start()



# API definitions
# PAGES
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        return render_template("login.html")


@app.route('/feed', methods=["POST"])
@page_requires_token
def get_feed(requesting_id=None):
    return render_template("feed.html")

@app.route('/error', methods=["GET"])
def error():
    return render_template("error.html")


# Authentication
@app.route('/users/new/standard', methods=["POST"])
def signup_standard():
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    first_name = request.form.get("firstname")
    last_name = request.form.get("lastname")

    force = request.form.get("force_request", False)

    if not all((username, password)) or not any((first_name, last_name)):
        return jsonify({"success": False, "error": "Required field empty."})
    else:
        if not first_name:
            first_name = last_name
            last_name = None
        db = DBHelper()
        result = db.add_user_standard(username, password, email=email, firstname=first_name, lastname=last_name, force=force)
        db.close_connection()
        success = result['success']

    if success:
        return jsonify({"success": True, "token": make_token(result["user_id"])})
    else:
        return jsonify({"success": False, "error": result["error"], "error_code":result["error_code"]})


@app.route('/users/login/standard', methods=["POST"])
def login_standard():
    username = request.form.get("username")
    password = request.form.get("password")

    if not all((username, password)):
        return jsonify({"success": False, "error": "Required field empty."})
    else:
        db = DBHelper()
        result = db.verify_user_password(username, password)
        db.close_connection()
        if result["result"]:
            return jsonify({"success": True, "token": make_token(result["user_id"])})
        else:
            return jsonify({"success": False, "error": result["message"]})


## press signup/login
@app.route('/users/oauthtoken/<provider_name>', methods=["POST", "GET"])
def signup_login_oauth(provider_name):

    auth = Auth(config=SOCIAL_CONFIG)

    # if success, return User object, else returns dict with error
    user = auth.auth_with_token(provider_name, request)
    if not isinstance(user, User):
        return jsonify({"success": False, "error": user.get("error")})
    else:
        # if success, return success json, else return error
        result = db.oauth_user(provider=provider_name, user=user)
        return jsonify({"success":True, "token": make_token(result.get("user_id")), "new_account":result.get("new_account")}) if result.get("result") else \
            jsonify({"success": False, "error": result.get("error")})





# CONTENT
@app.route('/clients/<requested_id>/calories/entries', methods=["GET"])
@api_requires_token
def get_calorie_entries(requested_id, requesting_id = None):
    #TODO add in query parameters
    #TODO validate sharing permissions

    db = DBHelper()
    db_results = db.get_calorie_entries(requested_id)
    db.close_connection()
    # db_results is still using named tuples, but CalorieEntry subquery made it no longer single object
    results = []
    for db_result in db_results:
        entry =db_result
        file = db_result.FileIndex
        result = {"timestamp":entry.timestamp, "image_id":entry.image_id, "client_comment":entry.client_comment,
                  "calories":entry.calories, "carb":entry.carb, "protein":entry.protein, "fat":entry.fat,
                  "trainer_comment":entry.trainer_comment, "reviewed":entry.reviewed, "food_name":entry.food_name,
                  "image_url":IMAGE_LOCATION_PREFIX+str(file.file_location)}
        results.append(result)

    # TODO consider distinguishing error between no user and no entries
    if results:
        return jsonify({"success":True, "results":results})
    else:
        return jsonify({"success": False, "error":"No results found."})


@app.route('/photos/<file_location>', methods=["GET"])
# @requires_token
def get_image_file(file_location, requesting_id=None):
    # TODO validate file permissions
    # TODO nginx file-accel goes here
    return send_from_directory("/Users/daniel/Downloads", filename=file_location)


# MESSAGING PLATFORMS
@app.route('/msgplatform/<platform_name>/new', methods=["POST"])
def log_new_message(platform_name):

    if platform_name not in list(MSG_PLATFORM_ID.keys()):
        return jsonify({"success":False, "error":"Invalid platform."}), 400

    response = make_response()
    file_list = request.files.getlist('image')
    image_path = None

    json_result = json.loads(request.form["json"])
    text =json_result.get("text")

    # TODO need to parse text and look for keywords/commands

    if file_list:
        # TODO consider resizing and compressing file
        file = file_list[0]
        ext = validate_image(file)
        if ext:
            file.filename = str(int(time.time())) + "_" + str(uuid.uuid4().time_low) + "." + ext

            image = Image.open(file)
            image_width = image.width
            image_height = image.height
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            if not os.path.isdir(FOOD_IMAGE_FOLDER):
                os.makedirs(FOOD_IMAGE_FOLDER, exist_ok=True)
            image_path = FOOD_IMAGE_FOLDER + "/" + secure_filename(file.filename)
            file.save(image_path)

            db = DBHelper()
            # save image and text to db and return
            result = db.add_new_msg(platform_name=platform_name, platform_username=json_result.get("username"), text=text,
                           image_type=IMAGE_TYPES.get("food"), file_location=file.filename, image_height=image_height,
                           image_width=image_width, image_size=file_size)
            db.close_connection()
            if result.get("result"):
                return jsonify({"success": True})
            else :
                return jsonify({"success": False, "error": result.get("error")})

    if not any((image_path, text)):
        return jsonify({"success":False, "error":"No text or images found."}), 400

    # if only text, save text and return
    db = DBHelper()
    result = db.add_new_msg(platform_name=platform_name, platform_username=json_result.get("username"), text=text,
                   image_type=None, file_location=None, image_height=None, image_width=None, image_size=None)
    db.close_connection()
    if result.get("result"):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result.get("error")})





if __name__ == '__main__':
    app.run()
