###################                                         1. DISEÑO DE LA BASE DE DATOS (SCHEMA)
# Grupo 03                                                  2. CONEXION: MONGODB, GOOGLE OAUTH, HTML 
###################                                         3. ESTRUCTURA DE LA APP
 
# Ángel García González
# Elena Raths Ponce
# Martín Millán Blanquez
# Ricardo Javier Fuentes Fino 


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
from mongoengine import StringField, DictField, BinaryField, ListField


app = Flask(__name__)
app.secret_key = "your-secret-key"


###################
# MongoDB
###################
client = MongoClient('mongodb+srv://Elena:Elena@geocachingapp.0sxhylv.mongodb.net/test')['Geocaching']

users = client.db.users
users_schema = {
    'name': StringField,
    'google_id': StringField, 
    #'games_played': ListField,
    #'games_created': ListField,
    #'role': ?   2
}

games = client.db.games
games_schema = {
    'name': StringField, # Overview
    'owner': StringField, # Creation
    'state': StringField, # Overview, Supervition  2
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
    'finder': StringField, #user 
}

#images = mongo.db.images
#images_schema = {
#    'image_data': BinaryField,  # Datos binarios de la imagen
#    'content_type': StringField,  # Tipo de contenido de la imagen (e.g. "image/jpeg")
#}


###################
# Google OAuth 
###################

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # Setting enviroment variable
GOOGLE_CLIENT_ID = "585245209475-ga6dg0vr7i5qjk1mopn8tgeb6ag5mv7j.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secrets.json")


flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

@app.route('/<path:path>')
def send_report(path):
    return send_from_directory('static', str(path))

def user_authentificated():
    if session['google_id']:
        return True
    else: 
        return login()

# Protects the app from unauthorized users
def login_is_required(function):
    def wrapper(*args, **kwargs): 
        if "google_id" not in session:
            return abort(401)  
        else:
            return function()
    return wrapper

# Redirects the user to the Google authenticator
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url() # Security feature
    session["state"] = state # Esures no third party has hooked on the request by savin state and session
    return redirect(authorization_url)

# Recieves the data from the Google endpoint
@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url) # Trades the recieved info for an access token to the api
    if not session["state"] == request.args["state"]: # Cecks if recieved state is the same as the state of the session
        abort(500) 
    credentials = flow.credentials # Safes credentials if successfull
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
    return redirect("/protected_area")

# Clear user session 
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Index html page
@app.route("/")
def index():
    return send_from_directory('static', 'index.html')

# Protected area, only visible for logged in users (gets executed from button to top)
@app.route("/protected_area") 
@login_is_required
def protected_area():
    return f"{session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"

@app.route('/create_game')
def create_game_page():
    return send_from_directory('static', 'create_game.html')

@app.route('/api/game', methods=['POST'])
def create_game():
    inserted=client['games'].insert_one({
        'name':request.form.get('name'), 
        #'owner':session['google_id'],
        'owner':'114755650557250667772',
        'topleft':int(request.form.get('topleft')),
        'bottomright':int(request.form.get('bottomright')),
    })
    return redirect('/game?id='+str(inserted.inserted_id))


###################
# Google Maps 
###################


if __name__ == "__main__":
    app.run(debug=True)