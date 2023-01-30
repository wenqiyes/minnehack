# Python standard libraries
import json
import os
import sqlite3
from urllib.parse import urlparse, quote
import cryptocode

# Third-party libraries
from flask import Flask, render_template, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
from jinja2 import StrictUndefined

# Internal imports
from google.db import init_db_command, get_db
from google.user import User

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.jinja_env.undefined = StrictUndefined

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def repeat_to_length(s, wanted):
  return (s * (wanted//len(s) + 1))[:wanted]

@app.route("/login",methods=["POST"])
def login():
  hash = cryptocode.encrypt(str(request.form.get("uname")),str(request.form.get("pwd")))
  user = User(
        id_=request.form.get("uname"), name=request.form.get("uname"), email=request.form.get("email"), profile_pic="", pwd=hash
    )
  return redirect("https://frontend.minnehackteam.repl.co/login_callback.html?token="+user.token)

@app.route("/verifyToken")
def verifyToken(token=None):
  db = get_db()
  token = db.execute(
    "SELECT * FROM valid_tokens WHERE token = ?", (token or request.args.get("token"))
  ).fetchone()
  if not token:
    resp = flask.Response("false")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
  del token
  resp = flask.Response("true")
  resp.headers['Access-Control-Allow-Origin'] = '*'
  return resp

@app.route("/getProjects")
def getProjects():
  return ""

@app.route("/login/google")
def googlelogin():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri="https://backend.minnehackteam.repl.co/login/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = quote(request.args.get("code"))
    print(code)
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    url = urlparse(request.url)
    url = url._replace(fragment="",scheme="https").geturl()
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=url,
        redirect_url="https://backend.minnehackteam.repl.co/login/callback",
        code=code
    )
    token_url = urlparse(token_url)
    token_url = token_url._replace(fragment="").geturl()
    print(token_url)
    print(headers)
    print(body)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    print(token_response.text)
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/")
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Login</a>'


@app.route("/projects/new", methods=["POST","GET"])
def newProject():
  token = request.form.get("token") or request.args.get("token")
  db = get_db()
  token = db.execute(
    "SELECT * FROM valid_tokens"#, (token,)
  ).fetchone()
  print(token)
  if token:
    open("projects/"+token.user)

@app.route("projects/<project_id>")
def show_project(project_id):
  db = get_db()
  project = db.execute(
    "SELECT * FROM projects WHERE project_id = project_id")
  if project:
    return render_template("project_details.html", project= project)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)