import urllib3, certifi
import json
from .user import User
from .oauth_classes import OAuth2

class GoogleAdapter(OAuth2):

    @staticmethod
    def auth_with_token(token=None):

        if not token:
            return False
        else :
            http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
            fields = {
                "id_token" : token
            }
            r = http.request("GET", "https://www.googleapis.com/oauth2/v3/tokeninfo", fields=fields)
            result = json.loads(r.data.decode('utf-8'))


            if not result.get("error_description"):
                id = result.get("sub")
                email = result.get("email")
                email_verified = result.get("email_verified")
                name = result.get('name')
                first_name = result.get('given_name')
                last_name = result.get('family_name')
                profile_pic = result.get('picture')

                return User(id, token, email=email, email_verified=email_verified, name=name, first_name=first_name,
                            last_name=last_name, profile_pic=profile_pic)
            else:
                return {"result": False, "error": result.get("error_description")}
