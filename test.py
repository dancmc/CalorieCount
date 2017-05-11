import requests
from flask import json
from databasehelper import DBHelper
from database import *
from d_oauth.oauth_classes import *

db = DBHelper()

fb_json = {
  "id": "10155365882286349",
  "name": "Daniel Chan",
  "email": "dcmc87@gmail.com",
  "first_name": "Daniel",
  "last_name": "Chan",
  "picture": {

  }
}

# url = 'http://localhost:5000/msgplatform/whatsapp/new'
# files = {'image': ('0.jpg', open('/Users/daniel/Downloads/0.jpg', 'rb'),'image/jpeg')}
# # r = requests.post(url, files=files, data = {"json":json.dumps({"password":"blahblah","username":"daniel"})})
#
print(db.session.query(MessagingPlatform).count())
db.add_new_msg("whatsapp", "p@whatsapp.com", "sdada", 22, "/Users/daniel/Downloads", 123, 311,31322)
print(db.session.query(MessagingPlatform).count())
