from flask import Flask, url_for, render_template, request, redirect, jsonify, make_response, json
import requests, os
import jwt, time, uuid
from PIL import Image
from werkzeug.utils import secure_filename
from whatsappclient import WhatsappInstance
from databasehelper import DBHelper
from config import *
from utils import *

from authomatic import Authomatic
from authomatic.adapters import WerkzeugAdapter

app = Flask(__name__)
db = DBHelper()
authomatic = Authomatic(config=SOCIAL_CONFIG,
                        secret="#\xf0\x07\x01\xc3C\x97J/\xf7\x8d\t\xdcR\r\x1er\xde|^\x98\xee\x0eK")


# listen for third party clients
WhatsappInstance().start()




# API definitions
# Pages
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        return render_template("signin.html")


@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route('/feed')
def signin():
    return render_template("home.html")


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
        result = db.add_user_standard(username, password, email=email, firstname=first_name, lastname=last_name, force=force)
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
        result = db.verify_user_password(username, password)
        if result["result"]:
            return jsonify({"success": True, "token": make_token(result["user_id"])})
        else:
            return jsonify({"success": False, "error": result["message"]})


## press signup/login
@app.route('/users/oauth/<provider_name>', methods=["POST", "GET"])
def signup_login_oauth(provider_name):
    ### get result
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name)

    if result:
        if result.user:
            result.user.update()
            if result.user.id:
                result = db.oauth_user(provider=provider_name, user=result.user)
                if result["result"]:
                    return jsonify({"success": True, "token": make_token(result["user_id"])})
                else:
                    return jsonify({"success":False, "error":result["message"]})

        else:
            return({"success":False, "error":"Failed to authenticate."})

    # returns a redirect to fb page first
    return response


# Content
@app.route('/clients/<requested_id>/calories/entries', methods=["GET"])
@requires_token
def get_calorie_entries(requested_id, requesting_id):
    #TODO add in query parameters
    #TODO validate sharing permissions
    entries = db.get_calorie_entries(requested_id)
    results = []
    for entry in entries:
        result = {"timestamp":entry.timestamp, "image_id":entry.image_id, "client_comment":entry.client_comment,
                  "calories":entry.calories, "carb":entry.carb, "protein":entry.protein, "fat":entry.fat,
                  "trainer_comment":entry.trainer_comment, "reviewed":entry.reviewed, "food_name":entry.food_name}
        results.append(result)

    # TODO consider distinguishing error between no user and no entries
    if results:
        return jsonify({"success":True, "results":results})
    else:
        return jsonify({"success": False, "error":"No results found."})



# Messaging Platforms
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

            # save image and text to db and return
            result = db.add_new_msg(platform_name=platform_name, platform_username=json_result.get("username"), text=text,
                           image_type=IMAGE_TYPES.get("food"), file_location=image_path, image_height=image_height,
                           image_width=image_width, image_size=file_size)
            if result.get("result"):
                return jsonify({"success": True})
            else :
                return jsonify({"success": False, "error": result.get("error")})

    if not any((image_path, text)):
        return jsonify({"success":False, "error":"No text or images found."}), 400

    # if only text, save text and return
    result = db.add_new_msg(platform_name=platform_name, platform_username=json_result.get("username"), text=text,
                   image_type=None, file_location=None, image_height=None, image_width=None, image_size=None)
    if result.get("result"):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result.get("error")})




def make_token(user_id):
    # TODO change expiry
    encoded = jwt.encode({'iss': 'dancmc.io',
                          'exp': int(time.time()) + 3600,
                          'id': user_id}, SECRET_KEY, algorithm='HS256')
    return encoded.decode()



if __name__ == '__main__':
    app.run()
