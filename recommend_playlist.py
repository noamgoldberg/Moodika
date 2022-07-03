import config as cfg
from urllib.parse import urlencode
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import logging

logging.basicConfig(filename=cfg.LOGFILE_NAME, format="%(asctime)s %(levelname)s: %(message)s",
                    level=logging.INFO)


def authorize():
    # Define the permissions scope of current user
    scope = "user-read-playback-state,user-modify-playback-state,playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cfg.CLIENT_ID,
                                                   client_secret=cfg.CLIENT_SECRET,
                                                   redirect_uri=cfg.REDIRECT_URI,
                                                   scope=scope))
    return sp


def recommend(param_dict, genre_list, sp, args):
    """
    Takes a dictionary of values for various audio parameters and returns a list of Spotify-recommended track URIs.
    """
    # Connecting to Spotify using client application
    # AUTH_RESPONSE = requests.post(cfg.AUTH_URL, {
    #     'grant_type': 'client_credentials',
    #     'client_id': cfg.CLIENT_ID,
    #     'client_secret': cfg.CLIENT_SECRET})
    #
    # # convert the response to JSON
    # AUTH_RESPONSE_DATA = AUTH_RESPONSE.json()
    #
    # # save the access token
    # ACCESS_TOKEN = AUTH_RESPONSE_DATA['access_token']
    #
    # # Use the access token to generate authorization
    # HEADERS = {'Authorization': 'Bearer {token}'.format(token=ACCESS_TOKEN)}
    # Define the permissions scope of current user

    #endpoint = f"{cfg.BASE_URL}/recommendations"
    #search_params = urlencode(param_dict)
    #lookup_url = f"{endpoint}?{search_params}"
    result = sp.recommendations(seed_genres=genre_list, limit=args.length, **param_dict)

    # Send a request to Spotify API using Spotipy
    # Iterate over response from Spotify, taking track URIs from recommended tracks
    print('Playlist')
    if result:
        track_uris = []
        for track in result['tracks']:
            print(f"Song: {track['name']}, Artist: {dict(track['album']['artists'][0])['name']}\n")
            track_uris.append(track['uri'])
    else:
        logging.warning(f"Nothing was returned from Spotify for url {param_dict}.")
        raise Exception("Nothing returned from Spotify.")
    return track_uris


def create_spotify_playlist(track_uris, input_text, sp):
    """
    Utilize Spotipy library to create a playlist given list of track URIs for current user
    """

    # Define username and playlist name to generate
    user_id = sp.me()['id']
    playlist_to_add = f"{input_text} - Moodika-generated"

    # Create playlist from given track URIs
    sp.user_playlist_create(user_id, playlist_to_add)
    playlists = sp.user_playlists(user_id)
    playlist_uid = playlists['items'][0]['id']
    playlist_link = f"https://open.spotify.com/playlist/{playlist_uid}"

    # Add tracks
    sp.playlist_add_items(playlist_uid, track_uris)
    logging.info(f"Spotify playlist '{playlist_to_add}' was created for Spotify user '{user_id}'.")

    print(playlist_link)
    return playlist_link
