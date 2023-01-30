from flask_login import UserMixin

from google.db import get_db

import cryptocode
from os import urandom
from codecs import encode

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, pwd):
        if self.get(id_,pwd):
          self = self.get(id_,pwd)
        else:
          self.create(id_, name, email, profile_pic, pwd)
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.pwd = pwd
        self.token = str(encode(urandom(64),'base64').strip()).replace("\n","").replace("==","").replace("b'","").replace("'","").replace(" ","").replace("\\","")
      
    def get(self, user_id, pwd):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        if cryptocode.decrypt(user[4],pwd) == user_id:
          self.__store_token()
          user = User(
            id_=user[0], name=user[1], email=user[2], profile_pic=user[3], pwd=user[4]
          )
          return user
        else:
          return None

    def create(self, id_, name, email, profile_pic, pwd):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, profile_pic, pwd) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_, name, email, profile_pic, pwd),
        )
        db.commit()
        self.__store_token()
    def __store_token(self):
      db = get_db()
      token = db.execute(
            "SELECT * FROM valid_tokens WHERE token = ?", (self.token)
        ).fetchone()
      if not token:
        db.execute(
            "INSERT INTO valid_tokens (token) "
            "VALUES (?)",
            (self.token),
        )
        db.commit()