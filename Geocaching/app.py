###################                                         
# Grupo 03                                                  
###################                                         
 
# Ángel García González
# Elena Raths Ponce
# Martín Millán Blanquez
# Ricardo Javier Fuentes Fino 


from flask import Flask, session, abort, redirect, request
from flask_pymongo import PyMongo
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import os
import pathlib
from mongoengine import connect
from mongoengine import StringField, DictField, ListField


app = Flask(__name__)
app.secret_key = "your-secret-key"


###################
# MongoDB
###################
mongo = PyMongo(app, uri="mongodb+srv://Elena:Elena@geocachingapp.0sxhylv.mongodb.net/test") # Contraseña?

users = mongo.db.users
users_schema = {
    'name': StringField,
    'google_id': StringField, 
    #'games_played': ListField,
    #'games_created': ListField,
    #'role': 
}

games = mongo.db.games
games_schema = {
    'name': StringField, # Overview
    'creator': StringField, # Creation
    'state': StringField, # Overview, Supervition
    'winner': StringField, # Overview
    'finalists': StringField, # Overview
    'area': DictField, # Creation
    'caches': ListField, # Creation, Supervition
    'map': ListField, # Supervition
}

caches = mongo.db.caches
caches_schema = {
    'name': StringField,
    'game': ListField, 
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
    return "<a href='/login'><button>Login</button></a>" # Return index.html

# Protected area, only visible for logged in users (gets executed from button to top)
@app.route("/protected_area") 
@login_is_required
def protected_area():
    return f"{session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"


###################
# Google Maps 
###################


if __name__ == "__main__":
    app.run(debug=True)