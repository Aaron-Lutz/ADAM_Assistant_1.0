from flask import Flask, request, jsonify, redirect, url_for, session
from flask import render_template
from requests_oauthlib import OAuth2Session
import os
import main
import requests
from gtts import gTTS
from flask import send_file
import re
from main import UserSession
from google.cloud import texttospeech
from google.oauth2 import service_account
import requests


# Set the OAUTHLIB_INSECURE_TRANSPORT environment variable to '1'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = os.urandom(24)  # set a secret key for session signing

client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
redirect_uri = "https://booming-oarlock-205714.oa.r.appspot.com/callback"  # This should match the redirect URI you registered

# This is Google's discovery document
discovery_url = "https://accounts.google.com/.well-known/openid-configuration"

def remove_urls(text):
    return re.sub(r'http\S+|www\.\S+', '', text)

def generate_tts_audio(text):
    cleaned_text = remove_urls(text)

    # Load the credentials from the JSON key file you downloaded
    credentials = service_account.Credentials.from_service_account_file('creds/tts_creds.json')

    # Create a client
    client = texttospeech.TextToSpeechClient(credentials=credentials)

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)

    # Build the voice request
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB", 
        name="en-GB-Neural2-D",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request
    voice = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save the audio to a file
    with open("output.mp3", "wb") as out:
        out.write(voice.audio_content)

    return voice.audio_content

def get_city_from_coordinates(latitude, longitude):
    response = requests.get(f'https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}')
    data = response.json()
    # The 'address' key in the JSON contains various details including city (named 'town' or 'city' depending on size)
    address = data.get('address', {})
    city = address.get('city', address.get('town', None))
    return city


@app.route("/")
def home():
    print("In home route")
    return render_template("index.html")  # replace with your HTML filename

@app.route("/login")
def login():
    print("In login route")
    scope = [
    'https://www.googleapis.com/auth/userinfo.profile', 
    'https://www.googleapis.com/auth/calendar', 
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/contacts.readonly'
    ]
    google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)


    # Fetch the OpenID configuration document
    oidc_config = requests.get(discovery_url).json()

    # Get the authorization endpoint from the config
    authorization_endpoint = oidc_config["authorization_endpoint"]

    # Use the authorization endpoint to get the authorization URL
    # Add access_type='offline' to request offline access
    # Add prompt='consent' to force the user to re-consent
    authorization_url, state = google.authorization_url(
        authorization_endpoint, 
        access_type='offline', 
        prompt='consent'
    )

    session["oauth_state"] = state  # Store the state for later use
    print(redirect_uri)  # Print the redirect URI to the console
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    print("In callback route")
    google = OAuth2Session(client_id, state=session["oauth_state"], redirect_uri=redirect_uri)
    token = google.fetch_token(
        token_url='https://oauth2.googleapis.com/token',
        client_secret=client_secret,
        authorization_response=request.url,
    )
    token['client_id'] = client_id
    token['client_secret'] = client_secret
    session["token"] = token  # Store the token for later use
    
    # Fetch user's profile and store the name in the session
    profile = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    session['user_name'] = profile.get('name')

    return redirect(url_for("home"))  # Redirect the user to the home page



   
@app.route('/process_command', methods=['POST'])
def process_command():
    print("In process_command route")

    # Get session data
    user_name = session.get('user_name')
    conversation_history = session.get('conversation_history', [])

    # Get data from request JSON payload
    data = request.get_json()
    prompt = data['prompt']
    token = session.get('token', None)
    
    # Store coordinates in the session
    session['latitude'] = data.get('latitude')
    session['longitude'] = data.get('longitude')
    
    # Get the city name from coordinates
    city_name = None
    if session['latitude'] and session['longitude']:
        city_name = get_city_from_coordinates(session['latitude'], session['longitude'])
    session['city'] = city_name  # Update the city in the session

    print(f"Prompt: {prompt}")
    
    # Pass conversation history and coordinates to process_command
    response, updated_conversation_history = main.process_command(user_name, prompt, token, conversation_history, session['latitude'], session['longitude'], city_name)
    
    # Update the conversation history in the session
    session['conversation_history'] = updated_conversation_history
    print(f"conversation history: {session['conversation_history']}")

    cleaned_response = remove_urls(response)
    
    generate_tts_audio(cleaned_response)

    return jsonify({'response': response})




@app.route('/get_intro_audio')
def get_intro_audio():
    intro_message = "Hello, I am Adam, your automated digital assistant mainframe! I am here to help you with your tasks and answer all your questions. I am still being developed, and you have access to an early version of myself. Currently, I am capable of performing web searches, giving weather updates, getting and adding events from and to your calendar, retrieving and sending your emails, and retrieving, adding, and deleting tasks. Login with your Google Account to grant me access to automate your every day life"
    
    generate_tts_audio(intro_message)
    
    return send_file("output.mp3", as_attachment=True)



@app.route('/get_audio')
def get_audio():
    return send_file("output.mp3", as_attachment=True)


@app.route("/profile")
def profile():
    print("In profile route")
    token = session.get("token")
    if not token:
        return redirect(url_for("login"))  # Redirect the user to the login page if they're not authenticated
    google = OAuth2Session(client_id, token=token)
    profile = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
	# Store the user's name in the session
    return jsonify(profile)

@app.route('/reset_chat', methods=['POST'])
def reset_chat():
    session['conversation_history'] = []  # Reset the conversation history
    return jsonify({}), 200  # Return a 200 status code



if __name__ == "__main__":
    app.run(debug=True)
