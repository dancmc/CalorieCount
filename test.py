import requests
from flask import json
from databasehelper import DBHelper

db = DBHelper()

url = 'http://localhost:5000/msgplatform/whatsapp/new'
files = {'image': ('0.jpg', open('/Users/daniel/Downloads/0.jpg', 'rb'),'image/jpeg')}
# r = requests.post(url, files=files, data = {"json":json.dumps({"password":"blahblah","username":"daniel"})})

db.add_new_msg("whatsapp", "p@whatsapp.com", "sdada", 22, "/Users/daniel/Downloads", 123, 311,31322)
