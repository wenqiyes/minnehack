import flask
from google.db import get_db
request = flask.request

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

@app.route("/projects/new", methods=["POST","GET"])
def newProject():
  token = request.form.get("token") or request.args.get("token")
  db = get_db()
  token = db.execute(
    "SELECT * FROM valid_tokens WHERE token = ?", (token)
  ).fetchone()
  print(token)
  if token:
    open("projects/"+token.user)

@app.route("projects/<project_id>")
def show_project(project_id)
  db = get_db()
  project = db.execute(
    "SELECT * FROM projects WHERE project_id = project_id")
  if project:
    return render_template("project_details.html", project= project)
  