from flask import Flask, render_template, redirect, request
from clients import SpotifyClient, GeniusClient
import os
from dotenv import load_dotenv

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
        return render_template('index.html')

@app.route('/login/')
def login():
    load_dotenv()
    try:
        spotify = SpotifyClient(scope='user-read-playback-state')
        auth_redirect = spotify.get_auth_redirect()
        return redirect(auth_redirect.url)

    except:
        return render_template('login_fail.html')

@app.route('/logged_in/')
def logged_in():
    load_dotenv()
    if os.environ.get('AUTH_CODE')==None:
        os.environ['AUTH_CODE'] = request.args.get('code')
        if os.environ.get('AUTH_CODE') is None:
            print('Warning! Authentication code not received.')
        spotify = SpotifyClient(scope='user-read-playback-state')
        spotify.get_and_set_tokens(os.environ.get('AUTH_CODE'))

    spotify = SpotifyClient(scope='user-read-playback-state')

    song_name, artist_name = spotify.currently_playing_info()

    genius = GeniusClient(os.environ.get('GENIUS_TOKEN'))
    song_lyrics = genius.get_lyrics(song_name, artist_name)

    return render_template('login_success.html', song_name=song_name, artist_name=artist_name, lyrics=song_lyrics)

if __name__ == '__main__':
    load_dotenv()
    app.run()
