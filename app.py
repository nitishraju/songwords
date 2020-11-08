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
    #loads local .env file with token details
    load_dotenv()
    try:
        #create Spotify client with permissions to read user's playback state
        spotify = SpotifyClient(scope='user-read-playback-state')

        #get redirect URL and redirect user
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

        # create Spotify client with permissions to read user's playback state
        spotify = SpotifyClient(scope='user-read-playback-state')
        spotify.get_and_set_tokens(os.environ.get('AUTH_CODE'))

    spotify = SpotifyClient(scope='user-read-playback-state')

    song_name, artist_name = spotify.currently_playing_info()

    # create Genius client and get lyrics
    genius = GeniusClient(os.environ.get('GENIUS_TOKEN'))
    song_lyrics = genius.get_lyrics(song_name, artist_name)

    #render template dynamically with lyrics from response
    return render_template('login_success.html', song_name=song_name, artist_name=artist_name, lyrics=song_lyrics)

if __name__ == '__main__':
    load_dotenv()
    app.run()
