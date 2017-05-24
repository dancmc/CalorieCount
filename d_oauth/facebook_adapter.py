import urllib3, certifi
import json
from .user import User
from .oauth_classes import OAuth2

class FacebookAdapter(OAuth2):

    @staticmethod
    def auth_with_token(token=None):

        print(token)
        if not token:
            return False
        else:
            http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
            fields = {
                "access_token": token,
                "fields" :"id,name,email, first_name, last_name, picture"
            }
            r = http.request("GET", "https://graph.facebook.com/me", fields=fields)
            result = json.loads(r.data.decode('utf-8'))


            if not result.get("error"):
                id = result.get("id")
                email = result.get("email")
                name = result.get('name')
                first_name = result.get('first_name')
                last_name = result.get('last_name')
                try:
                    profile_pic = result.get('picture').get("data").get("url")
                except AttributeError:
                    profile_pic = None

                return User(id, token, email=email, email_verified=False, name=name, first_name=first_name,
                            last_name=last_name, profile_pic=profile_pic)
            else:
                return {"result":False, "error":result.get("error").get("message"), "error_code":1}