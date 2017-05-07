from database import *
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import relationship, sessionmaker
from flask import request
from itertools import chain
import time
from config import *
import traceback

connection = None

class DBHelper:
    def __init__(self):
        self.engine = create_engine('mysql://root:@localhost:3306/calorie', echo=False)
        self.connection = self.engine.connect()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def close_connection(self):
        try:
            self.connection.close()
        except:
            pass


    def add_user_standard(self, username, password, email = None, firstname=None, lastname=None, force=False):
        # TODO add other form fields
        def adduser():

            user = User(username=username, first_name=firstname, last_name=lastname, email=email)
            user.hash_password(password)

            self.session.add(user)
            self.session.commit()

            return {"success": True, "user_id": user.user_id}


        if bool(self.session.query(User).filter_by(username=username).count()):
            return {"success":False, "error":"Username already exists.", "error_code":1}
        elif email:
            q1 = self.session.query(SocialLogin.email_verified).filter_by(email=email)
            q2 = self.session.query(User.email_verified).filter_by(email=email)
            # union eliminates duplicates, so at most 2 True/False results
            result = chain.from_iterable(q1.union(q2).all())

            if result:
                if any(result):
                    return {"success":False, "error":"Email is already registered.", "error_code":2}
                elif force:
                    return adduser()
                else:
                    return {"success":False, "error":"Account with similar unverified email already exists, continue with creating new account?", "error_code":3}
            else:
                return adduser()
        else:
            return adduser()

    def oauth_user(self, provider, user):

        ### check if id is already in table -- return JWT with assoc user_id
        result = self.session.query(SocialLogin).filter_by(provider_id=provider,provider_user_id=user.provider_user_id).first()
        if result:
            return {"result":True, "user_id" : result.user_id, "new_account":False}

        #### if id not in table - check if email is already in either table
        else:
            q1 = self.session.query(SocialLogin.email).filter_by(email=user.email)
            q2 = self.session.query(User.email).filter_by(email=user.email)
            result = q1.union(q2).count()

            ##### if email in tables (cannot trust social email) - say email already registered, please link social from account management
            ##### should not auto link accounts or create new account
            if result:
                return {"result":False, "message":"Email already registered, please login using another method and link %s account from account management" % provider.capitalize()}
            ##### if email not in tables - create a new account and send JWT
            else:
                rawconn = self.engine.raw_connection()
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

                    cursor = rawconn.cursor()
                    cursor.callproc("add_new_oauth", [fname, lname, provider, str(user.provider_user_id), user.email,
                                                      user.credentials.token, user.credentials.token_secret])

                    rowsinserted = cursor.rowcount
                    new_user_id = cursor._rows[0][0]

                    cursor.close()
                    rawconn.commit()
                except:
                    return {"result":False, "error" : "Failed DB operation"}
                finally:
                    rawconn.close()
            if rowsinserted:
                return {"result":True, "user_id":new_user_id, "new_account":True}
            else:
                return {"result": False, "error": "Failed DB operation"}

    def verify_user_password(self, username, password):
        user = self.session.query(User).filter_by(username=username).first()
        if user:
            if user.verify_password(password=password):
                return {"result":True, "user_id":user.user_id}
            else:
                return {"result": False, "error": "Password invalid."}
        else:
            return {"result":False, "error":"Could not find specified username."}

    def add_new_msg(self, platform_name, platform_username, text, image_type, file_location, image_height, image_width, image_size):
        # check if username exists and get user_id
        kw = {platform_name:platform_username}
        result = self.session.query(User.user_id).filter_by(**kw).first()

        # TODO parse message for special non food commands
        if not result:
            return {"result": False, "error": "User not registered."}
        else:
            user_id = result[0]
            rawconn = self.engine.raw_connection()

            try:
                cursor = rawconn.cursor()
                # TODO need to add file permissions for trainers in proc
                cursor.callproc("add_client_message_calorie", [user_id, MSG_PLATFORM_ID.get(platform_name), platform_username,
                                                               text, image_type, file_location, image_height, image_width,
                                                               image_size, time.time()])

                rowsinserted = cursor.rowcount
                new_calorie_entry = cursor._rows[0][0]
                print(new_calorie_entry)


                cursor.close()
                rawconn.commit()
                return {"result":True, "calorie_entry":new_calorie_entry}
            except:
                traceback.print_exc()
                return {"result": False, "error": "Failed DB operation"}
            finally:
                rawconn.close()

    def user_exists(self, user_id):
        result = self.session.query(User).filter_by(user_id=user_id).count()
        return bool(result)

    def get_calorie_entries(self, user_id):
        result = self.session.query(CalorieEntry).filter_by(user_id=user_id).order_by(CalorieEntry.timestamp.desc()).all()
        return result

