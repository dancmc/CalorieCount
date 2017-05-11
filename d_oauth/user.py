
class User:
    def __init__(self, id, token, secret=None, email=None, name=None, first_name=None, last_name=None, profile_pic=None, email_verified=False):
        self.id = id
        self.token = token
        self.secret=secret if secret else None
        self.email=email if email else None
        self.name = name if name else None
        self.first_name = first_name if first_name else None
        self.last_name = last_name if last_name else None
        self.profile_pic = profile_pic if profile_pic else None
        self.email_verified=email_verified if email_verified else False
