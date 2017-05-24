import urllib3, certifi
import json
from .user import User
from .oauth_classes import OAuth1


class TwitterAdapter(OAuth1):

    @staticmethod
    def auth_with_token(request=None):

        if not request:
            return False
        else:
            verification_url = request.headers.get("X-Auth-Service-Provider")
            if not verification_url or not verification_url.startswith("https://api.twitter.com"):
                return False
            oauth_params = request.headers.get("X-Verify-Credentials-Authorization")

            http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
            headers = {
                "Authorization": oauth_params
            }
            r = http.request("GET", verification_url, headers=headers)
            result = json.loads(r.data.decode('utf-8'))

            # TODO adjust error json based on request testing
            if not result.get("errors"):
                id = result.get("id")
                email = result.get("email")
                email_verified = bool(email)
                name = result.get('name')
                profile_pic = result.get('profile_image_url_https')


                return User(id, None, email=email, email_verified=False, name=name, first_name=None,
                            last_name=None, profile_pic=profile_pic)
            else:
                return False
