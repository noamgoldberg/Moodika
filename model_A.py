from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)
import pandas as pd
import sys
import base64
from recommend_playlist import *
from config import *
from parse_args import *
import logging

#
# def authorize():
#     sp = spotipy.Spotify(
#         auth_manager=spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))
#     return sp


def get_token():
    # Authorization
    url = "https://accounts.spotify.com/api/token"
    headers2 = {}
    data = {}

    # Encode as Base64
    message = f"{CLIENT_ID}:{CLIENT_SECRET}"
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    base64Message = base64Bytes.decode('ascii')

    headers2['Authorization'] = f"Basic {base64Message}"
    data['grant_type'] = "client_credentials"
    r = requests.post(url, headers=headers2, data=data)
    token = r.json()['access_token']
    return token


BASE_URL = 'https://api.spotify.com/v1'
HEADERS = {'Authorization': 'Bearer {token}'.format(token=get_token())}


def raise_spotify_error():
    raise Exception(f'Error. Trouble connecting to Spotify. Try a different input phrase.')


def generate_params(args, num_playlists=10, print_steps=False):
    input_text = args.text
    sp = authorize()

    # (1) Get all playlist uris from playlists in search results
    playlists_results = sp.search(q=input_text, limit=num_playlists, type='playlist')['playlists']
    playlist_uris = [playlist['id'] for playlist in playlists_results['items']]
    if print_steps:
        print("Playlist URIs (list of strings):", playlist_uris)

    # (2) Get all track uris from playlists in search results
    track_results = [sp.playlist_items(p_uri, limit=100) for p_uri in playlist_uris]
    if len(track_results) == 0:
        raise_spotify_error()
    track_uris_dict = {playlist_uris[i]: [track['track']['id'] if track['track'] is not None else None for track in track_results[i]['items']] for i in range(len(playlist_uris))}
    track_uris_dict = {key: [track_uri for track_uri in track_uris_dict[key] if track_uri] for key in track_uris_dict}
    if print_steps:
        print("Track URIs (dict):\n", track_uris_dict)

    # (3) Get audio features of each track in each playlist
    audio_features = [sp.audio_features(tracks=track_uris_dict[playlist]) for playlist in track_uris_dict]
    audio_features = [[{f: track[f] for f in AUDIO_FEATURES_TO_EXTRACT} for track in playlist] for playlist in
                      audio_features]
    avg_audio_features = dict(pd.concat([pd.DataFrame(audio_features[i]).mean() for i in range(len(playlist_uris))],
                                        axis=1).mean(axis=1))
    avg_audio_features['popularity'] = args.popularity
    if print_steps:
        print("Features averaged (series):\n", avg_audio_features)
    return avg_audio_features


def main(print_steps=False):
    args = parse_args(sys.argv[1:])
    if print_steps:
        print("Parsed args:", args)
    if args.command == 'input':
        try:
            sp = authorize()
            genre_text = predict_genre(args)
            params = generate_params(args, num_playlists=10, print_steps=print_steps)
            if print_steps:
                print("Spotify params:", params)
            tracks = recommend(params, genre_text, sp, args)
            if print_steps:
                print("tracks:", tracks)
            create_spotify_playlist(tracks, args.text, sp)
        except ValueError as e:
            print('ValueError:', e)
            logging.critical(e)
        except AttributeError as e:
            print('AttributeError:', e)
            logging.critical(e)
        except TypeError as e:
            print('TypeError:', e)
            logging.critical(e)
        except Exception as e:
            logging.critical(e)
    return


# def generate_playlist(search_params):
#     endpoint = f"{BASE_URL}/recommendations"
#     lookup_url = f"{endpoint}?{search_params}"
#     print(lookup_url)
#     r = requests.get(lookup_url, headers=HEADERS)
#     print('Playlist')
#     if r:
#         track_uris = []
#         for track in r.json()['tracks']:
#             print(f"Song: {track['name']}, Artist: {dict(track['album']['artists'][0])['name']}\n")
#             track_uris.append(track['uri'])


if __name__ == '__main__':
    main(print_steps=True)
