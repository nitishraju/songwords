import requests
import sys
import os
import base64
import bs4
from flask import Markup

class SpotifyClient:
    def __init__(self, scope=None):
        self.scope = scope
        self.redirect_uri = 'http://127.0.0.1:5000/logged_in/'

    def get_id_and_secret(self):
        if os.environ.get('CLIENT_ID') == None or os.environ.get('CLIENT_SECRET') == None:
            print('Warning! CLIENT_ID or CLIENT_SECRET has not been set.')
        return os.environ.get('CLIENT_ID'), os.environ.get('CLIENT_SECRET')

    def get_refresh_token(self):
        if os.environ.get('REFRESH_TOKEN')==None:
            print('Warning! Refresh token is set to None.')
        return os.environ.get('REFRESH_TOKEN')

    def get_redirect_uri(self):
        if self.redirect_uri == None:
            print('Warning! Redirect URI set to None.')
        return self.redirect_uri

    def get_access_token(self):
        if os.environ.get('SPOTIFY_TOKEN')==None:
            print('Warning! Spotify access token is set to None.')
        return os.environ.get('SPOTIFY_TOKEN')

    def get_auth_redirect(self):
        # get redirect address from GET request
        auth_params = {'client_id': self.get_id_and_secret()[0],
                       'response_type': 'code',
                       'redirect_uri': self.get_redirect_uri(),
                       'scope': self.scope}
        try:
            auth_redirect = requests.get('https://accounts.spotify.com/authorize', params=auth_params)
            return auth_redirect

        except requests.exceptions.HTTPError:
            print('Please recheck your initialization parameters.')
            sys.exit()

    def get_and_set_tokens(self, auth_code):
        auth_code = auth_code
        # POST request for token data
        token_data = {'code': auth_code,
                      'grant_type': 'authorization_code',
                      'redirect_uri': self.get_redirect_uri()}
        client_creds = '{0}:{1}'.format(*self.get_id_and_secret())
        token_header = {'Authorization': 'Basic {}'.format(base64.urlsafe_b64encode(client_creds.encode()).decode())}
        token_response = requests.post('https://accounts.spotify.com/api/token', data=token_data, headers=token_header)

        # parsing POST response
        try:
            os.environ['SPOTIFY_TOKEN'] = token_response.json()['access_token']
            os.environ['REFRESH_TOKEN'] = token_response.json()['refresh_token']
        except KeyError:
            print('Error in getting tokens.')
            print(token_response.json())
        else:
            print('Access and refresh token set.')

    def refresh_access_token(self):
        client_creds = '{0}:{1}'.format(*self.get_id_and_secret())

        data = {'refresh_token': self.get_refresh_token(),
                'grant_type': 'refresh_token'}
        headers = {'Authorization': 'Basic {}'.format(base64.urlsafe_b64encode(client_creds.encode()).decode())}
        response = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)

        if response.status_code == requests.codes.ok:
            os.environ['SPOTIFY_TOKEN'] = response.json()['access_token']
            print('Refreshed access token.')
        else:
            print(response)
            print('The access token expired.')

    def currently_playing_info(self):
        self.refresh_access_token()
        headers = {'Authorization': 'Bearer ' + self.get_access_token()}
        song_response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)

        song_name = song_response.json()['item']['name']
        artist_name = song_response.json()['item']['artists'][0]['name']
        return song_name, artist_name


class GeniusClient:
    def __init__(self, access_token):
        self.access_token = access_token

    def get_lyrics(self, song_title, artist_name):
        #takes in song title and artist name and sends GET search request to API
        base_url = 'https://api.genius.com'
        headers = {'Authorization': 'Bearer ' + self.access_token}
        search_url = base_url + '/search'
        data = {'q': song_title + ' ' + artist_name}
        response = requests.get(search_url, data=data, headers=headers)

        #getting search results from response
        search_results = response.json()['response']['hits']

        # collecting lyric webpage URL by comparing search result song and artist names with Spotify data
        for item in search_results:
            item_title = item['result']['title']
            item_artist = item['result']['primary_artist']['name']
            print('Genius: ' + item_title + ', Spotify: ' + song_title)

            if (song_title in item_title) or (item_title in song_title) or (artist_name in item_artist) or (item_artist in artist_name):
                lyric_url = item['result']['url']
                break

        #making soup from Genius lyric_url data
        try:
            sdata = requests.get(lyric_url).text
            soup = bs4.BeautifulSoup(sdata, 'html.parser')
            #extracting lyrics in html format from soup
            html_lyrics_div = soup.find("div", class_='lyrics')
            html_lyrics = html_lyrics_div.get_text()
            lyric_list = html_lyrics.replace('\n', '<br>')
        except UnboundLocalError:
            return 'lyrics not found :('

        return Markup(lyric_list)