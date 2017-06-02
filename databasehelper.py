from database import *
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from flask import request
from itertools import chain
import time
from config import *
import traceback


# connection = None


class DBHelper:
    def __init__(self):
        self.engine = create_engine('mysql://root:@localhost:3306/calorie', echo=False)
        # self.connection = self.engine.connect()
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        # TODO might need to create new sessions for each request
        self.session = self.Session()
        Base.metadata.create_all(self.engine)

    # def close_connection(self):
    #     try:
    #         self.connection.close()
    #     except:
    #         pass


    def add_user_standard(self, username, password, email=None, firstname=None, lastname=None, force=False):
        # TODO add other form fields
        def adduser():

            user = User(username=username, first_name=firstname, last_name=lastname, email=email)
            user.hash_password(password)

            self.session.add(user)
            self.session.commit()

            return {"result": True, "user_id": user.user_id}

        if bool(self.session.query(User).filter_by(username=username).count()):
            return {"result": False, "error": "Username already exists.", "error_code": 1}
        elif email:
            q = self.session.query(User.email_verified).filter_by(email=email).all()
            result = list(chain.from_iterable(q))

            # if any emails from db match
            if result:
                # if a matching email is verified
                if any(result):
                    return {"result": False, "error": "Email is already registered.", "error_code": 2}
                # if there is matching unverified email but user wants to continue
                elif force:
                    return adduser()
                # if there is matching unverified email
                else:
                    return {"result": False,
                            "error": "Account with similar unverified email already exists, continue with creating new account?",
                            "error_code": 3}
            else:
                return adduser()
        else:
            return adduser()

    def oauth_user(self, provider, user, force=False):

        def add_user():
            from utils import random_b64_string, download_image
            try:
                name = user.name
                fname = user.first_name
                lname = user.last_name

                if not fname:
                    if lname:
                        fname = lname
                        lname = None
                    else:
                        fname = name


                file_id=None
                image_ob=None
                if user.profile_pic:
                    image_name = random_b64_string(32) + ".jpg"
                    file_index_ob = FileIndex(filename=image_name, file_type=FILE_TYPES.get("image"))
                    self.session.add(file_index_ob)
                    self.session.flush()
                    file_id = file_index_ob.file_id

                    image_ob = download_image(user.profile_pic, image_name, file_id=file_id,
                                              image_type=IMAGE_TYPES.get("profile"))


                user_ob = User(email=user.email, first_name=fname, last_name=lname, profile_pic_id=file_id)
                self.session.add(user_ob)
                self.session.flush()

                if file_id:
                    self.session.add(FilePermission(file_id=file_id, user_id=user_ob.user_id))
                if image_ob:
                    image_ob.uploader_id = user_ob.user_id
                    self.session.add(image_ob)

                social_login = SocialLogin(user_id=user_ob.user_id, provider_id=provider,
                                             provider_user_id=str(user.id),
                                             access_token=user.token)
                self.session.add(social_login)
                self.session.commit()

                return {"result": True, "user_id": user_ob.user_id, "new_account": True, "email": user.email}
            except:
                print(traceback.print_exc())
                return {"result": False, "error": "Failed DB operation.", "error_code":200}

        # check if id is already in table -- return JWT with assoc user_id
        result = self.session.query(SocialLogin).filter_by(provider_id=provider, provider_user_id=user.id).first()
        if result:
            return {"result": True, "user_id": result.user_id, "new_account": False}

        # if id not in table - check if email is already in either table
        elif user.email:
            q = self.session.query(User.email_verified).filter_by(email=user.email).all()
            result = list(chain.from_iterable(q))

            # if email in tables (cannot trust social email) - say email already registered, please link social from account management
            # should not auto link accounts or create new account
            if result:
                # if matching verified email
                if any(result):
                    return {"result": False,
                            "error": "Email already registered, please login using another method and link %s account from account management." % provider.capitalize(),
                            "error_code":201}
                # if there is matching unverified email but user wants to continue
                elif force:
                    return add_user()
                # if there is matching unverified email
                else:
                    return {"result": False,
                            "error": "Account with similar unverified email already exists, continue with creating new account?",
                            "error_code": 202}
            # if email not in tables - create a new account and send JWT
            else:
                return add_user()

        # if no email provided
        else:
            return add_user()

    def verify_user_password(self, username, password):
        # can log in with email or username
        if "@" in username:
            user = self.session.query(User).filter_by(email=username, email_verified=True).first()
        else:
            user = self.session.query(User).filter_by(username=username).first()

        if user:
            if user.verify_password(password=password):
                return {"result": True, "user_id": user.user_id}
            else:
                return {"result": False, "error": "Password invalid.", "error_code":200}
        else:
            if "@" in username:
                return {"result": False, "error": "Could not find matching verified email.", "error_code":201}
            else:
                return {"result": False, "error": "Could not find specified username.", "error_code":203}

    def add_new_msg(self, platform_name, platform_username, text, image_type, filename, image_height, image_width,
                    image_size):
        # check if username exists and get user_id
        kw = {platform_name: platform_username}
        result = self.session.query(User.user_id).filter_by(**kw).first()

        new_calorie_entry = None
        if not result:
            return {"result": False, "error": "User not registered."}

        # if user exists, add entry to calorie entries, messaging_platforms, images [optional]
        else:
            user_id = result[0]
            try:
                # TODO need to add file permissions for trainers in proc
                timestamp = int(time.time() * 1000)
                fileindex = None
                if image_type:
                    file = FileIndex(filename=filename, file_type=FILE_TYPES.get("image"))
                    self.session.add(file)
                    self.session.flush()
                    fileindex = file.file_id

                    image = Image(image_id=fileindex, uploader_id=user_id, image_type=image_type,
                                  image_height=image_height, image_width=image_width, image_size=image_size)
                    file_permission = FilePermission(file_id=fileindex, user_id=user_id)
                    self.session.add_all([image, file_permission])

                messaging_platform = MessagingPlatform(username=platform_username,
                                                       platform_id=MSG_PLATFORM_ID.get(platform_name),
                                                       timestamp=timestamp, image_id=fileindex, text=text)
                calorie_entry = CalorieEntry(user_id=user_id, timestamp=timestamp, image_id=fileindex,
                                             client_comment=text)
                self.session.add_all([messaging_platform, calorie_entry])
                self.session.commit()
                new_calorie_entry = calorie_entry.id

            except:
                print(traceback.print_exc())

        # return id of new calorie entry
        return {"result": True, "calorie_entry": new_calorie_entry} if new_calorie_entry else {"result": False,
                                                                                               "error": "Failed DB operation"}

    def add_new_entry_calorie(self, user_id, text, image_type, filename, image_height, image_width, image_size):

        # check if user_id exists
        result = self.session.query(User.user_id).filter_by(user_id=user_id).first()

        new_calorie_entry = None
        # if user does not exist
        if not result:
            return {"result": False, "error": "User not registered."}

        # if user exists, need to add entry to calorie entries, images [optional]
        else:
            try:

                fileindex = None
                if image_type:
                    file = FileIndex(filename=filename, file_type=FILE_TYPES.get("image"))
                    self.session.add(file)
                    self.session.flush()
                    fileindex = file.file_id
                    image = Image(image_id=fileindex, uploader_id=user_id, image_type=image_type,
                                  image_height=image_height, image_width=image_width, image_size=image_size)
                    file_permission = FilePermission(file_id=fileindex, user_id=user_id)
                    self.session.add_all([image, file_permission])

                entry = CalorieEntry(user_id=user_id, timestamp=int(time.time() * 1000), image_id=fileindex,
                                     client_comment=text)
                self.session.add(entry)
                self.session.commit()
                new_calorie_entry = entry.id

            except:
                print(traceback.print_exc())

        # return id of new calorie entry
        return {"result": True, "calorie_entry": new_calorie_entry} if new_calorie_entry else {"result": False,
                                                                                               "error": "Failed DB operation.", "error_code":200}

    def user_exists(self, user_id):
        result = self.session.query(User).filter_by(user_id=user_id).count()
        return bool(result)

    def messaging_username_exists(self, service, username):
        kw = {service: username, service + "_verified": True}
        user_id = self.session.query(User.user_id).filter_by(**kw).first()
        return bool(user_id)

    def get_calorie_entries(self, user_id, entries_from=None, entries_to=None, reviewed=None,
                            calories_above=None, calories_below=None, page=1):

        page = 1 if page is None else int(page)
        offset = (page - 1) * 25

        if reviewed:
            reviewed = bool(reviewed.lower() == "true")
        sq = self.session.query(CalorieEntry).filter_by(user_id=user_id)
        sq = sq if entries_from is None else sq.filter(CalorieEntry.timestamp >= int(entries_from))
        sq = sq if entries_to is None else sq.filter(CalorieEntry.timestamp <= int(entries_to))
        sq = sq if reviewed is None else sq.filter_by(reviewed=reviewed)
        sq = sq if calories_above is None else sq.filter(CalorieEntry.calories > int(calories_above))
        sq = sq if calories_below is None else sq.filter(CalorieEntry.calories < int(calories_below))
        sq = sq.subquery()

        entries = self.session.query(sq, FileIndex).filter(sq.c.image_id == FileIndex.file_id).order_by(
            sq.c.timestamp.desc()).slice(offset, offset + 26).all()
        return entries

    def register_messaging_service(self, service, user_id, service_username, verified=False):
        rows_updated = self.session.query(User).filter_by(user_id=user_id) \
            .update({service: service_username, service + "_verified": verified}, synchronize_session=False)
        self.session.commit()

        return {"result": True} if rows_updated else {"result": False, "error": "No matching user ID found."}

    def validate_relationship(self, client_id, trainer_id):
        return bool(self.session.query(ClientTrainer).filter_by(client_id=client_id, trainer_id=trainer_id).count())

    def register_otp(self, otp, user_id, purpose, data, timestamp=int(time.time() * 1000)):
        entry = OTP(otp=otp, user_id=user_id, purpose=purpose, data=data, timestamp=timestamp)
        self.session.add(entry)
        self.session.commit()

        return {"result": True} if entry.id else {"result": False}

    def validate_otp(self, otp, user_id, purpose, data, valid_duration=900000):
        if user_id:
            entry = self.session.query(OTP).filter_by(otp=otp, user_id=user_id, purpose=purpose).filter(
                OTP.data.like("%" + data + "%")).order_by(OTP.timestamp.desc()).first()
        else:
            entry = self.session.query(OTP).filter_by(otp=otp, purpose=purpose).filter(
                OTP.data.like("%" + data + "%")).order_by(OTP.timestamp.desc()).first()
        valid_cutoff = int(time.time() * 1000) - valid_duration

        if not entry:
            return {"result": False, "error": "No matching OTP and user."}
        if entry.timestamp < valid_cutoff:
            return {"result": False, "error": "OTP expired, request a new one."}
        else:
            return {"result": True, "entry": entry}

    def get_trainerlist(self, user_id):
        entries = self.session.query(ClientTrainer.trainer_id).filter_by(client_id=user_id).all()
        result = []
        for entry in entries:
            result.append({"user_id": entry.trainer_id})

        return result

    def verify_email(self, user_id, email):
        existing = self.session.query(User).filter_by(email=email, email_verified=True).first()
        if existing:
            return {"result": False, "error": "This email has been verified before."}
        rows_updated = self.session.query(User).filter_by(user_id=user_id) \
            .update({"email": email, "email_verified": True}, synchronize_session=False)
        self.session.commit()

        return {"result": True} if rows_updated else {"result": False, "error": "No matching user ID found."}

    def get_user_from_username(self, username):
        result = self.session.query(User).filter_by(username=username).first()
        return result

    def get_user_from_email(self, email):

        users = self.session.query(User).filter_by(email=email).all()

        # if no emails matching
        if not users:
            return {"result": False, "error": "No matching verified email.", "error_code":200}

        # if able to find verified email
        for user in users:
            if user.email_verified:
                if user.username:
                    return {"result": True, "user_id": user.user_id}
                else:
                    socials = user.social_logins
                    soc = []
                    for social in socials:
                        soc.append(social.provider_id)
                    if soc:
                        return {"result": True, "user_id": user.user_id, "social_logins": soc}

        # if multiple unverified emails
        if len(users) > 1:
            return {"result": False, "error": "No matching verified email.", "error_code":200}
        # if single unverified email
        elif len(users) == 1:
            return {"result": True, "user_id": users[0].user_id}

    def get_user_details(self, user_id, fields):

        user = self.session.query(User).filter_by(user_id=user_id).first()

        if user:
            whatsapp = None if user.whatsapp is None else user.whatsapp.split("@")[0]

            soc = []
            c = []
            t = []

            socials = user.social_logins
            for social in socials:
                soc.append({"network": social.provider_id, "network_user_id": social.provider_user_id})

            if "relationships" in fields:
                clients = user.clients
                for client in clients:
                    c.append({"id": client.client_id})
                trainers = user.trainers
                for trainer in trainers:
                    t.append({"id": trainer.trainer_id})


            return {"result": True,
                    "user": {"user_id": user.user_id, "username": user.username, "email": user.email,
                             "email_verified": user.email_verified, "first_name": user.first_name,
                             "last_name": user.last_name, "mobile_number": user.mobile_num,
                             "profile_pic": IMAGE_LOCATION_PREFIX+user.profile_pic,
                             "whatsapp": whatsapp, "whatsapp_verified": user.whatsapp_verified,
                             "time_joined": user.time_joined,
                             "default_homepage": user.default_homepage,
                             "social_logins": soc, "clients":c, "trainers":t}}
        else:
            return {"result": False, "error": "No user found."}
