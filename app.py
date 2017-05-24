from flask import Flask, url_for, render_template, request, redirect, jsonify, make_response, json, send_from_directory, \
    Response
import requests, os, jwt, time
from random import randint
from base64 import b64encode
from PIL import Image
from werkzeug.utils import secure_filename
from whatsappclient import WhatsappInstance
from databasehelper import DBHelper
from config import *
from mailhandler import *
from utils import *
from flask_cors import CORS
from flask_mail import Mail, Message
from Crypto.Cipher import AES
from urllib import parse

from d_oauth.auth import Auth
from d_oauth.user import User

app = Flask(__name__)
app.config.from_object('defaultsettings')

mail = Mail(app)
CORS(app)
db = DBHelper()


# listen for third party clients
# w = WhatsappInstance()
# w.start()


# API definitions
# PAGES
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        return render_template("login.html")


@app.route('/feed', methods=["POST"])
@requires_token
def get_feed(requesting_id=None):
    return render_template("feed.html")


@app.route('/error', methods=["GET"])
def error():
    return render_template("error.html")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Authentication
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@app.route('/users/new/standard', methods=["POST"])
def signup_standard():
    # TODO may need to require email verification to complete signup to prevent spam
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    first_name = request.form.get("firstname")
    last_name = request.form.get("lastname")

    # if prompted that unverified email exists in system
    force = request.form.get("force_request", False)

    if not all((username, password, email)) or not any((first_name, last_name)):
        return jsonify({"success": False, "error": "Required field empty.", "error_code":4}), 400
    else:
        if not first_name:
            first_name = last_name
            last_name = None
        result = db.add_user_standard(username, password, email=email, firstname=first_name, lastname=last_name,
                                      force=force)

    if not result or not result.get("result"):
        return jsonify({"success": False, "error": result.get("error"), "error_code": result.get("error_code")})
    else:
        user_id = result.get("user_id")
        # if mobile/server, must include api key, otherwise will assume is a website with cookies
        if request.form.get("api_key"):
            out = jsonify({"success": True, "token": make_user_token(
                {"user_id": user_id, "api_key": request.form.get("api_key")})})
        else:
            out = jsonify({"success": True, "token": make_csrf_token({"user_id": user_id})})
            out.set_cookie('user_token', make_user_token({"user_id": user_id}), httponly=True)

        if email:
            send_verification_email(True, user_id, email)
        return out


@app.route('/users/login/standard', methods=["POST"])
def login_standard():
    username = request.form.get("username")
    password = request.form.get("password")

    if not all((username, password)):
        return jsonify({"success": False, "error": "Required field empty.", "error_code":1}), 400
    else:
        result = db.verify_user_password(username, password)

    if not result.get("result"):
        return jsonify({"success": False, "error": result.get("error"), "error_code":result.get("error_code")})
    else:
        if request.form.get("api_key"):
            out = jsonify({"success": True, "token": make_user_token(
                {"user_id": result["user_id"], "api_key": request.form.get("api_key")})})
        else:
            out = jsonify({"success": True, "token": make_csrf_token({"user_id": result["user_id"]})})
            out.set_cookie('user_token', make_user_token({"user_id": result.get("user_id")}), httponly=True)
        return out


## press signup/login
@app.route('/users/oauthtoken/<provider_name>', methods=["POST"])
def signup_login_oauth(provider_name):
    auth = Auth(config=SOCIAL_CONFIG)
    force = request.form.get("force_request", False)

    # validate provider name
    if provider_name not in SOCIAL_CONFIG:
        return jsonify({"success": False, "error": "Invalid provider.", "error_code": 3}), 400

    # if validated by external server, return User object, else returns dict with error
    user = auth.auth_with_token(provider_name, request)
    if not isinstance(user, User):
        if user.get("error_code") ==1:
            return jsonify({"success": False, "error": "Failed OAuth with provider.", "error_code":1}), 500
        elif user.get("error_code") ==2:
            return jsonify({"success": False, "error": "Server error.", "error_code":2}), 500
    else:
        # check if user already exists in db
        result = db.oauth_user(provider=provider_name, user=user, force=force)
        if not result or not result.get("result"):
            return jsonify({"success": False, "error": result.get("error"), "error_code":result.get("error_code")}), 409
        else:
            if result.get("new_account") and result.get("email"):
                send_verification_email(True, result.get("user_id"), result.get("email"))

            # if request from mobile/server
            if request.form.get("api_key"):
                out = jsonify({"success": True, "new_account": result.get("new_account"), "token": make_user_token(
                    {"user_id": result.get("user_id"), "api_key": request.form.get("api_key")})})
            # if request from website
            else:
                out = jsonify({"success": True, "new_account": result.get("new_account"),
                               "token": make_csrf_token({"user_id": result.get("user_id")})})
                out.set_cookie('user_token', make_user_token({"user_id": result.get("user_id")}), httponly=True)
            return out


@app.route('/users/validate_credentials', methods=["POST"])
@requires_token
def validate_credentials(requesting_id=None):
    cookie = request.cookies.get("user_token")
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        payload = jwt.decode(cookie, USER_TOKEN_SECRET, algorithms=['HS256'])
    else:
        payload = decode_header(auth_header, USER_TOKEN_SECRET).get("payload")

    return jsonify({"success": True, "payload": payload})


@app.route('/users/verify_email', methods=["GET"])
def verify_email():
    string = request.args.get("code")

    # try and decode argument with userid and OTP
    try:
        jsondict = decrypt_dict_des(EMAIL_VERIFY_ENC_KEY, string)
        user_id = jsondict.get("user_id")
    except:
        # TODO create templates
        return render_template("email_verify_fail.html", "Link not valid.")

    if user_id:
        result = db.validate_otp(jsondict.get("code"), user_id, "email", "", get_milli(days=1))
        if result.get("result"):
            verify = db.verify_email(user_id, result.get("entry").data)
            if verify.get("result"):
                return render_template("email_verify_success.html")
            else:
                return render_template("email_verify_fail.html", verify.get("error"))
        else:
            return render_template("email_verify_fail.html", result.get("error"))

    return render_template("email_verify_fail.html", "Failed verification, try requesting again.")


@app.route('/users/request_email_verification', methods=["POST"])
@requires_token
def request_verify_email(requesting_id=None):
    email = request.form.get("email")
    if isinstance(email, str) and "@" in email:
        send_verification_email(False, requesting_id, email)
        return {"success": True, "message": "Verification email sent to " + email}
    else:
        return {"success": False, "error": "Invalid email submitted."}, 400


@app.route('/users/forgot_login', methods=["POST"])
def forgot_login():
    username = request.form.get("username")

    if not username:
        return jsonify({"success": False, "error": "Invalid username submitted."}), 400

    if "@" in username:
        result = db.get_user_from_email(username)
        if result.get("result"):
            if result.get("social_logins"):
                send_recovery_email(None, username, result.get("social_logins"))
            else:
                send_recovery_email(result.get("user_id"), username, None)
            return jsonify({"success": True, "message": "Email sent to registered email."})
        else:
            return jsonify({"success": False, "error": result.get("error"), "error_code": result.get("error_code")}), 404
    else:
        user = db.get_user_from_username(username)
        if not user:
            return jsonify({"success": False, "error": "Username not found.", "error_code":1}), 404
        elif user.email:
            send_recovery_email(user.user_id, user.email, None)
            return jsonify({"success": True, "message": "Email sent to registered email."})
        else:
            return jsonify({"success": False, "error": "No email associated with username.", "error_code":2}), 404


@app.route('/users/recover_account', methods=["GET"])
def recover_account():
    string = request.args.get("code")

    # try and decode argument with userid and OTP
    try:
        jsondict = decrypt_dict_des(EMAIL_RECOVERY_ENC_KEY, string)
        user_id = jsondict.get("user_id")
    except:
        # TODO create templates
        return render_template("account_recovery_fail.html", "Link not valid.")

    if user_id:
        result = db.validate_otp(jsondict.get("code"), user_id, "recover", "", get_milli(hours=1))
        if result.get("result"):
            print("success")
            db.verify_email(user_id, result.get("entry").data)
            return render_template("account_recovery_reset_pw.html")
        else:
            return render_template("account_recovery_fail.html", result.get("error"))

    return render_template("account_recovery_fail.html", "Failed verification, try requesting again.")


@app.route('/users/register_msgplatform/<platform>', methods=["POST"])
@requires_token
def register_whatsapp(platform, requesting_id=None):

    platform_id = request.form.get("platform_id")

    if platform not in ["whatsapp", "line", "wechat"]:
        return jsonify({"success": False, "error": "Invalid platform.", "error_code":1}), 400
    if not platform_id:
        return jsonify({"success": False, "error": "No platform ID submitted.", "error_code": 2}), 400

    otp = randint(100000, 999999)

    result = db.register_otp(otp, requesting_id, "whatsapp", str(platform_id), int(time.time() * 1000))
    db.register_messaging_service("whatsapp", requesting_id, platform_id, False)

    return jsonify({"success": True, "otp": otp}) if result["result"] else jsonify({"success": False})


# CONTENT
@app.route('/clients/<requested_id>/calories/entries', methods=["GET"])
@requires_token
def get_calorie_entries(requested_id, requesting_id=None):
    # parse query parameters
    # ints
    if requested_id == "self":
        requested_id = requesting_id
    entries_from = request.args.get("from")
    entries_to = request.args.get("to")
    recent = request.args.get("recent")
    calories_above = request.args.get("cal_above")
    calories_below = request.args.get("cal_below")
    page = request.args.get("page")
    # bools
    reviewed = request.args.get("reviewed")
    # strings
    sort_by = request.args.get("sort_by")

    if not validate_positive_ints(requested_id, entries_from, entries_to, recent, calories_above, calories_below, page,
                                  accept_none=True):
        return jsonify({"success": False, "error": "Bad parameter - not a positive integer."}), 400
    if not validate_boolean(reviewed, accept_none=True):
        return jsonify({"success": False, "error": "Bad parameter - reviewed is not a boolean."}), 400
    # TODO if not sort_by.lower() in [None, "time", ]

    requested_id = int(requested_id)

    # validate sharing permissions
    if not requested_id == requesting_id and not db.validate_relationship(requested_id, requesting_id):
        return jsonify({"success": False, "error": "No permissions to view requested resource."}), 401

    entries = db.get_calorie_entries(requested_id, entries_from, entries_to, reviewed, calories_above, calories_below,
                                     page)
    # db_results is still using named tuples, but CalorieEntry subquery made it no longer single object
    results = []
    for entry in entries:
        file = entry.FileIndex
        image_url = IMAGE_LOCATION_PREFIX + str(file.filename) if file.filename else None
        result = {"timestamp": entry.timestamp, "image_id": entry.image_id, "client_comment": entry.client_comment,
                  "calories": entry.calories, "carb": entry.carb, "protein": entry.protein, "fat": entry.fat,
                  "trainer_comment": entry.trainer_comment, "reviewed": entry.reviewed, "food_name": entry.food_name,
                  "image_url": image_url}
        results.append(result)

    return jsonify({"success": True, "results": results, "page": page, "has_next_page": bool(len(entries) > 25)})


@app.route('/clients/<requested_id>/calories/recent', methods=["GET"])
@requires_token
def get_calorie_entries_recent(requested_id, requesting_id=None):
    pass


# for now no validation of individual image permissions - trust that image names unguessable and relationship level ->
# permissions are validated in list requests
@app.route('/photos/<filename>', methods=["GET"])
def get_image_file(filename, requesting_id=None):
    # TODO validate file permissions
    # TODO nginx file-accel goes here
    return send_from_directory("/Users/daniel/Downloads", filename=filename)


@app.route('/clients/<user_id>/entry/calorie/new', methods=["POST"])
@requires_token
def new_calorie_entry(user_id, requesting_id=None):
    # TODO @userinput
    if user_id == "self":
        user_id = requesting_id
    elif validate_postive_int(user_id):
        user_id = int(user_id)
    else:
        return jsonify({"success": False, "error": "User ID does not exists, or no permission for this resource."}), 400

    # check that users posting to own feed
    if user_id != requesting_id:
        return jsonify({"success": False, "error": "Users can only post photos to their own feed."}), 403

    # extract images and json from POST body
    image_list = request.files.getlist("image")
    request_json = request.json if request.json else request.form.get("json")
    json_dict = json.loads(request_json)
    filename = None
    result = None

    text = json_dict.get("text")

    # if there are images
    if image_list:
        image = image_list[0]
        ext = validate_image(image)
        if ext:
            saved = save_image(FOOD_IMAGE_FOLDER,image, ext)
            filename = saved.get("filename")

            # TODO save image to database
            # save image and text to db and return
            result = db.add_new_entry_calorie(user_id=user_id,
                                              text=text,
                                              image_type=IMAGE_TYPES.get("food"), filename=filename,
                                              image_height=saved.get("image_height"),
                                              image_width=saved.get("image_width"), image_size=saved.get("image_size"))

    # if no text or images
    elif not any((filename, text)):
        return jsonify({"success": False, "error": "No text or images found."}), 400
    else:
        # if only text, save text and return
        result = db.add_new_entry_calorie(user_id=user_id, text=text,
                                          image_type=None, filename=None, image_height=None, image_width=None,
                                          image_size=None)

    if result and result.get("result"):
        image_url = IMAGE_LOCATION_PREFIX + filename if filename else None
        res = {"image_url": image_url}
        return jsonify({"success": True, "result": res}), 200
    else:
        return jsonify({"success": False, "error": result.get("error") if result else "Unknown error."}), 500


@app.route('/clients/self/trainerlist', methods=["GET"])
@requires_token
def get_trainer_list(requesting_id=None):
    try:
        result = db.get_trainerlist(requesting_id)
    except:
        result = None

    if result is not None:
        return jsonify({"success": True, "trainers": result, "total": len(result)}), 200
    else:
        return jsonify({"success": False, "error": "DB error.", "error_code":1}), 500


@app.route('/users/self', methods=["GET"])
@requires_token
def get_user_details(requesting_id=None):
    inclusions = request.args.get("include")

    allowed_fields = ["relationships"]
    parsed_fields = []

    if inclusions:
        inclusions = parse.unquote(inclusions).split(",")
        for field in inclusions:
            if field in allowed_fields:
                parsed_fields.append(field)

    result = db.get_user_details(requesting_id, parsed_fields)
    if result.get("result"):
        return jsonify({"success": True, "user": result.get("user")})
    else:
        return jsonify({"success": False, "error": result.get("error")})


# MESSAGING PLATFORMS
@app.route('/msgplatform/<platform_name>/new', methods=["POST"])
def log_new_message(platform_name):
    # TODO add secret identifier to POST requests
    if platform_name not in list(MSG_PLATFORM_ID.keys()):
        return jsonify({"success": False, "error": "Invalid platform."}), 400

    image_list = request.files.getlist('image')
    request_json = request.json if request.json else request.form.get("json")
    json_dict = json.loads(request_json)
    filename = None
    result = None

    # TODO @userinput
    text = json_dict.get("text")
    test_text = text.lower()
    username = json_dict.get("username")

    # check if username is registered
    if not db.messaging_username_exists(platform_name, username) and not test_text.startswith("register"):
        return jsonify({"success": False, "error": "User not registered."})

    # parse text for keywords
    # TODO need to parse text and look for keywords/commands
    if test_text.startswith("register"):
        otp = test_text.split(" ")[1]
        if platform_name == "whatsapp":
            whatsapp_number = username.split("@")[0][-6:]
            result = db.validate_otp(otp, None, "whatsapp", whatsapp_number)
            if result.get("result"):
                entry = result.get("entry")
                user_id = entry.user_id
                rego = db.register_messaging_service("whatsapp", user_id, username, True)

                if rego.get("result"):
                    return jsonify({"success": True, "message": "User successfully registered."})
                else:
                    return jsonify({"success": False, "error": rego.get("error")})
            else:
                # TODO reply to whatsapp with registration failure
                pass

    # if there are images
    if image_list:
        # TODO consider resizing and compressing file
        image = image_list[0]
        ext = validate_image(image)
        if ext:
            saved = save_image(FOOD_IMAGE_FOLDER, image, ext)
            filename = saved.get("filename")

            # save image and text to db and return
            result = db.add_new_msg(platform_name=platform_name, platform_username=username,
                                    text=text,
                                    image_type=IMAGE_TYPES.get("food"), filename=filename,
                                    image_height=saved.get("image_height"),
                                    image_width=saved.get("image_width"), image_size=saved.get("image_size"))

    elif not any((filename, text)):
        return jsonify({"success": False, "error": "No text or images found."}), 400
    else:
        # if only text, save text and return
        result = db.add_new_msg(platform_name=platform_name, platform_username=json_dict.get("username"), text=text,
                                image_type=None, filename=None, image_height=None, image_width=None, image_size=None)

    if result and result.get("result"):
        image_url = IMAGE_LOCATION_PREFIX + filename if filename else None
        res = {"image_url": image_url}
        return jsonify({"success": True, "result": res}), 200
    else:
        return jsonify({"success": False, "error": result.get("error") if result else "Unknown error."}), 500


def send_verification_email(first_time, user_id, email):
    subject = "Welcome!" if first_time else "Email Verification"
    otp = random_b64_string(16)
    db.register_otp(otp, user_id, "email", email)

    jsondict = {"user_id": user_id, "code": otp}
    send_email(("Admin", "admin@dancmc.io"), [email], subject,
               "Please validate your email here : "
               "" + DOMAIN + "/users/verify_email?code=" + encrypt_dict_des(EMAIL_VERIFY_ENC_KEY, jsondict))


def send_recovery_email(user_id, email, social_logins):
    # if sending recovery link
    if user_id:
        otp = random_b64_string(16)
        db.register_otp(otp, user_id, "recover", email)

        jsondict = {"user_id": user_id, "code": otp}
        send_email(("Admin", "admin@dancmc.io"), [email], "Account Recovery",
                   "Please click here to set a new password : "
                   "" + DOMAIN + "/recover_account?code=" + encrypt_dict_des(EMAIL_RECOVERY_ENC_KEY, jsondict))

    # if sending reminder of social logins
    else:
        soc = " & ".join(social_logins)
        pronoun = "it" if len(social_logins) == 1 else "them"
        send_email(("Admin", "admin@dancmc.io"), [email], "Account Recovery",
                   "You signed up with " + soc + ", please use " + pronoun + " to log in.\nAlternatively, please contact our support staff.")


if __name__ == '__main__':
    app.run()
