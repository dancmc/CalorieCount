from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TEXT, BIGINT, SMALLINT, BOOLEAN, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

from passlib.hash import argon2

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    user_id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(TEXT(30))
    email = Column(TEXT(255))
    email_verified = Column(BOOLEAN, default=False)
    password_hash = Column(TEXT(255))
    first_name = Column(TEXT(255), nullable=False)
    last_name = Column(TEXT(255))
    mobile_num = Column(TEXT(255))
    profile_pic = Column(TEXT(255))
    whatsapp = Column(TEXT(255))
    line = Column(TEXT(255))
    wechat = Column(TEXT(255))
    time_joined = Column(BIGINT)
    active = Column(BOOLEAN)
    default_homepage = Column(INTEGER)
    default_login = Column(TEXT(16))

    def hash_password(self, password):
        self.password_hash = argon2.hash(password)

    def verify_password(self, password):
        return argon2.verify(password, self.password_hash)


class SocialLogin(Base):
    __tablename__ = 'social_logins'

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(INTEGER, ForeignKey('users.user_id'), nullable=False)
    # facebook
    provider_id = Column(TEXT(255), nullable=False)
    # result.user.id
    provider_user_id = Column(TEXT(255), nullable=False)
    # result.user.email
    email = Column(TEXT(255))
    email_verified = Column(BOOLEAN, default=False)
    # result.user.credentials.token
    access_token = Column(TEXT(255))
    # result.user.credential.token_secret
    secret = Column(TEXT(255))
    # result.user.name, first_name, last_name
    # TODO if no first name and last name, then use name


    # profile_url = "http://facebook.com/profile.php?id=%s" % profile['id']
    # image_url = "http://graph.facebook.com/%s/picture" % profile['id']



class ClientTrainer(Base):
    __tablename__ = 'client_trainer'

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    client_id = Column(INTEGER, ForeignKey('users.user_id'))
    trainer_id = Column(INTEGER, ForeignKey('users.user_id'))
    trainer_type = Column(SMALLINT(unsigned=True))
    start_time = Column(BIGINT)
    end_time = Column(BIGINT)

# TODO file index needs more metadata
class FileIndex(Base):
    __tablename__ = 'file_index'

    file_id = Column(INTEGER, autoincrement=True, primary_key=True)
    file_location = Column(VARCHAR(255))

class Image(Base):
    __tablename__ = 'images'

    image_id = Column(INTEGER, ForeignKey('file_index.file_id'),primary_key=True)
    uploader_id = Column(INTEGER, ForeignKey('users.user_id'))
    image_type = Column(SMALLINT(unsigned=True))
    # may not need
    file_location = Column(VARCHAR(255))
    image_height = Column(SMALLINT)
    image_width = Column(SMALLINT)
    image_size = Column(INTEGER)


class FilePermission(Base):
    __tablename__ = 'file_permissions'

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    file_id = Column(INTEGER, ForeignKey('file_index.file_id'))
    user_id = Column(INTEGER, ForeignKey('users.user_id'))

class CalorieEntry(Base):
    __tablename__ = 'calorie_entries'

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(INTEGER, ForeignKey('users.user_id'))
    food_name = Column(TEXT(255))
    timestamp = Column(BIGINT)
    image_id = Column(INTEGER)
    client_comment = Column(TEXT)
    calories = Column(SMALLINT(unsigned=True))
    carb = Column(SMALLINT(unsigned=True))
    protein = Column(SMALLINT(unsigned=True))
    fat = Column(SMALLINT(unsigned=True))
    trainer_comment = Column(TEXT)
    reviewed = Column(BOOLEAN, default=False)

class DataPermission(Base):
    __tablename__='calorie_permissions'

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    client_id = Column(INTEGER, ForeignKey('users.user_id'))
    trainer_id = Column(INTEGER, ForeignKey('users.user_id'))
    data_type = Column(SMALLINT(unsigned=True))

class MessagingPlatform(Base):
    __tablename__ = 'messaging_platforms'

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(TEXT(255))
    platform_id = Column(SMALLINT(unsigned=True))
    timestamp = Column(BIGINT)
    image_id = Column(INTEGER)
    text = Column(TEXT)