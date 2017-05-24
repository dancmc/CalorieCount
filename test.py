import requests
from flask import json
import requests
from databasehelper import DBHelper
from database import *
from d_oauth.oauth_classes import *
from werkzeug.utils import secure_filename
import os, random, time, timeit
from base64 import urlsafe_b64encode, urlsafe_b64decode, b64decode, b64encode
from utils import *
from Crypto.Cipher import AES
from cryptography.fernet import Fernet, MultiFernet

import hashlib

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
# print(db.session.query(MessagingPlatform).count())
# db.add_new_msg("whatsapp", "p@whatsapp.com", "sdada", 22, "/Users/daniel/Downloads", 123, 311,31322)
# print(db.session.query(MessagingPlatform).count())

# start=time.time()
# print(b64encode(os.urandom(8)).decode("utf-8"))
# print(b64encode(os.urandom(16)).decode("utf-8"))
# print(urlsafe_b64encode(os.urandom(32)).decode("utf-8"))
# print(b64encode(os.urandom(64)).decode("utf-8"))
# print(time.time()-start)

# def do():
#     url = 'http://localhost:5000/users/validate_credentials'
#     headers = {"Authorization":"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJkYW5jbWMuaW8iLCJ1c2VyX2lkIjozLCJleHAiOjE0OTUwNDYyNDV9.W_2O02GB9OMrWWW1hSiHbkvE-YCuP3zSEfkrQzocTd4"}
#     r = requests.post(url, headers=headers, cookies={"user_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJkYW5jbWMuaW8iLCJ1c2VyX2lkIjozLCJleHAiOjE0OTUwNDYyNDV9.vu6nhL8RwvIfsorvEr3n-vzd0xXkJvUHE9emgMGIGjI"})
#
# a = timeit.timeit(do, number=1)
# print(a)

# results = db.get_calorie_entries(3, page=1)
# print(bool(len(results)>25))
# for result in results:
#     print(result.id)
# sort = None
# print(sort in [])


# def factorial(n):
#     l = [a for a in range(1,n+1)]
#     result = 1
#     for num in l:
#         result*=num
#     return result
#
# def combinations(numbers=0, letters=0, symbols=0):
#     total = 10**numbers * 52**letters * 10**symbols
#     permutations = factorial(numbers+letters+symbols)
#     permutations_identical = permutations/factorial(numbers)/factorial(letters)/factorial(symbols)
#     total *=permutations_identical
#     return total
#
# print(combinations(numbers=10,letters=0, symbols=0))
# print(combinations(numbers=6,letters=1, symbols=1))
#
# print(2**2900)
download_image("http://i.imgur.com/M2u7Ipx.png", "blah.png")




