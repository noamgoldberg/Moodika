import config as cfg
from urllib.parse import urlencode
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials


def recommend(param_dict):
    AUTH_RESPONSE = requests.post(cfg.AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': cfg.CLIENT_ID,
        'client_secret': cfg.CLIENT_SECRET})

    # convert the response to JSON
    AUTH_RESPONSE_DATA = AUTH_RESPONSE.json()

    # save the access token
    ACCESS_TOKEN = AUTH_RESPONSE_DATA['access_token']

    HEADERS = {'Authorization': 'Bearer {token}'.format(token=ACCESS_TOKEN)}
    endpoint = f"{cfg.BASE_URL}/recommendations"
    search_params = urlencode(param_dict)
    lookup_url = f"{endpoint}?{search_params}"

    print(lookup_url)
    r = requests.get(lookup_url, headers=HEADERS)

    print('Playlist')
    if r:
        track_uris = []
        for track in r.json()['tracks']:
            print(f"Song: {track['name']}, Artist: {dict(track['album']['artists'][0])['name']}\n")
            track_uris.append(track['uri'])
    else:
        raise Exception("Nothing returned from Spotify")

    return track_uris


def create_spotify_playlist(track_uris, input_text):
    scope = "user-read-playback-state,user-modify-playback-state,playlist-modify-public"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cfg.CLIENT_ID,
                                                   client_secret=cfg.CLIENT_SECRET,
                                                   redirect_uri=cfg.REDIRECT_URI,
                                                   scope=scope))

    user_id = sp.me()['id']
    playlist_to_add = f"{input_text} - Moodika-generated"

    # Create playlist
    sp.user_playlist_create(user_id, playlist_to_add)
    playlists = sp.user_playlists(user_id)
    playlist_uid = playlists['items'][0]['id']

    print(f"https://open.spotify.com/playlist/{playlist_uid}")

    # Add tracks
    sp.playlist_add_items(playlist_uid, track_uris)
