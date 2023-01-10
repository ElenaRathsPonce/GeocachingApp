from flask import Flask, session, abort, redirect, request, send_from_directory
from flask_pymongo import PyMongo, MongoClient
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import os
import pathlib
from mongoengine import connect
from mongoengine import StringField, DictField, ListField
from bson.objectid import ObjectId


app = Flask(__name__,template_folder='templates')
app.secret_key = "your-secret-key"


#########################
# MongoDB
#########################
client = MongoClient('mongodb+srv://Elena:Elena@geocachingapp.0sxhylv.mongodb.net/test')['Geocaching']

users = client.db.users
users_schema = {
    'name': StringField,
    'google_id': StringField, 
}

games = client.db.games
games_schema = {
    'name': StringField, # Overview
    'owner': StringField, # Creation
    'state': StringField, # Overview, Supervition
    'winner': StringField, # Overview
    'finalists': ListField, # Overview
    'area': DictField, # Creation
    'caches': ListField, # Creation, Supervition
}

caches = client.db.caches
caches_schema = {
    'name': StringField,
    'location': DictField,
    'hint': DictField,
    'state': StringField,
    'finder': StringField,
    'game_id': StringField,
}


#########################
# Google OAuth 
#########################

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # Setting enviroment variable
GOOGLE_CLIENT_ID = "585245209475-ga6dg0vr7i5qjk1mopn8tgeb6ag5mv7j.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secrets.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

#@app.route('/<path:path>')
def send_report(path):
    return send_from_directory('templates', str(path))

# Check authentificated user
def user_authentificated():
    if session['google_id']:
        return True
    else: 
        return login()

# Protect app from unauthorized users
def login_is_required(function):
    def wrapper(*args, **kwargs): 
        if "google_id" not in session:
            return abort(401)  
        else:
            return function()
    return wrapper

# Redirect user to the Google authentificator
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url() # Security feature
    session["state"] = state # Esure no third party has hooked on the request by savin state and session
    return redirect(authorization_url)

# Recieve data from the Google endpoint
@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url) # Trade the recieved info for an access token to the api
    if not session["state"] == request.args["state"]: # Ceck if recieved state is the same as the state of the session
        abort(500) 
    credentials = flow.credentials # Safe credentials if successfull
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    result = list(client['users'].find(
        filter= {'google_id': id_info.get("sub")}
    ))
    if len(result) == 0: 
        client['users'].insert_one({'google_id':id_info.get("sub"), 'name':id_info.get("name")})
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    # Once logged in, the users can navigate in a protected area
    return redirect("/game_overview")

# Clear user session 
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


#########################
# Interface & Functions 
#########################

# App homepage
@app.route("/")
def index():
    return send_from_directory('templates', 'index.html')

# Log out page
@app.route("/clear_session")
@login_is_required
def clear_session():
    return f"{session['name']} <br/> <a href='/logout'><button>Logout</button> </a>"


# Game creation page
@app.route('/create_game')
#@login_is_required
def create_game():
    return send_from_directory('templates', 'create_game.html')

# Create a game
@app.route('/api/create', methods=['POST'])
def create():
    inserted=client['games'].insert_one({
        'name': request.form.get('name'), 
        #'owner':session['google_id'],
        'owner':'114755650557250667772',
        'topleft':int(request.form.get('topleft')),
        'bottomright':int(request.form.get('bottomright')),
    })
    return redirect('/game?id='+str(inserted.inserted_id))

# Pagina para editar el juego 
@app.route('/game')
#@login_is_required
def game():
    return send_from_directory('templates', 'game.html')

# Create caches
@app.route('/api/create_caches/<string:game_id>/', methods=['POST'])
def create_caches(game_id):
    inserted = client['geo'].insert_one({
        'long': int(request.form.get('long')),
        'lat': int(request.form.get('lat')),
    })
    client['caches'].insert_one({
        'name': request.form.get('name'),
        'location': str(inserted.inserted_id),
        'hint': request.form.get('hint'),
        'state': False,
        'game_id':game_id,
    })
    return redirect('/game?id='+str(game_id))

@app.route('/game/<string:game_id>/caches')
def game_caches(game_id):
    html=""
    caches=list(client['caches'].find(filter={"game_id":game_id}))
    for cache in caches:
        html += """<br/><p>"""+cache["name"]+"""<a href='/api/delete_cache/"""+str(cache['_id'])+"""'>delete</a></p>"""
    return html

@app.route('/api/delete_cache/<string:cache_id>')
def delete_cache(cache_id):
    cache=client['caches'].find_one(filter={"_id":ObjectId(cache_id)})
    client['caches'].delete_one(filter={"_id":ObjectId(cache_id)})
    return game_caches(cache['game_id'])

@app.route('/game_overview')
#@login_is_required
def game_overview():
    return send_from_directory('templates', 'game_overview.html')

@app.route('/user_games')
def user_games():
    html='<ul>'
    games=list(client['games'].find(filter={'owner':session['google_id']}))
    for game in games:
        html+="<li><a href='/game?id="+str(game['_id'])+"'>"+game['name']+"</a></li>"
    return html + "</ul>"


#########################
# Google Maps 
#########################


if __name__ == "__main__":
    app.run(debug=True)