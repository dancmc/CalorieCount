from authomatic.providers import oauth2, oauth1

SECRET_KEY = "\x1a)\xab\x85\xf8b\x1ae\x82r\xde\xac\x14p\x12\xe4\xa06\x89-\x04\xceU\xd8"

SOCIAL_CONFIG = {

    'twitter': {  # Your internal provider name

        # Provider class
        'class_': oauth1.Twitter,

        # Twitter is an AuthorizationProvider so we need to set several other properties too:
        'consumer_key': '########################',
        'consumer_secret': '########################',
    },

    'facebook': {

        'class_': oauth2.Facebook,

        # Facebook is an AuthorizationProvider too.
        'consumer_key': '167489697111129',
        'consumer_secret': '2760e0fab8ad28138bd17d4d479b194f',

        # But it is also an OAuth 2.0 provider and it needs scope.
        'scope': ['email'],
    },

    'google': {
        'class_': oauth2.Google,
        'consumer_key': '',
        'consumer_secret': ''
    }
}

MSG_PLATFORM_ID = {
    'whatsapp': 0,
    'facebook': 1,
    'line': 2,
    'wechat': 3
}

IMAGE_TYPES = {
    'food':1
}

IMAGE_LOCATION_PREFIX = "http://localhost:5000"

FOOD_IMAGE_FOLDER = "/Users/daniel/Downloads"
