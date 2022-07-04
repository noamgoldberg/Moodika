from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)
import pandas as pd
import sys
import os
from recommend_playlist import *
from config import *
from parse_args import *
import logging

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def raise_spotify_error():
    raise Exception(f'Nothing Returned from Spotify. Try using different input.')


def generate_params(args, num_playlists=10, verbose=0):
    input_text = args.text
    sp = authorize()

    # (1) Get all playlist uris from playlists in search results
    playlists_results = sp.search(q=input_text, limit=num_playlists, type='playlist')['playlists']
    # print("playlist_results:", playlists_results)
    playlist_uris = [playlist['id'] for playlist in playlists_results['items']]
    if verbose > 0:
        print("Playlist URIs (list of strings):", playlist_uris)

    # (2) Get all track uris from playlists in search results
    track_results = [sp.playlist_items(p_uri, limit=100) for p_uri in playlist_uris]
    if len(track_results) == 0:
        raise_spotify_error()
    track_uris_dict = {playlist_uris[i]: [track['track']['id'] if track['track'] is not None else None for track in track_results[i]['items']] for i in range(len(playlist_uris))}
    track_uris_dict = {key: [track_uri for track_uri in track_uris_dict[key] if track_uri] for key in track_uris_dict}
    if verbose > 0:
        print("Track URIs (dict):\n", track_uris_dict)

    # (3) Get audio features of each track in each playlist
    audio_features = [sp.audio_features(tracks=track_uris_dict[playlist]) for playlist in track_uris_dict]
    audio_features = [[track_features for track_features in playlist if track_features] for playlist in track_uris_dict]
    print('audio_features:', audio_features)
    audio_features = [[{f: track[f] for f in AUDIO_FEATURES_TO_EXTRACT} for track in playlist] for playlist in
                      audio_features]
    avg_audio_features = dict(pd.concat([pd.DataFrame(audio_features[i]).mean() for i in range(len(playlist_uris))],
                                        axis=1).mean(axis=1))
    avg_audio_features['popularity'] = args.popularity
    if verbose > 0:
        print("Features averaged (series):\n", avg_audio_features)
    return avg_audio_features


def main(verbose=0):
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    args = parse_args(sys.argv[1:])
    if verbose > 0:
        print("Parsed args:", args)
    if args.command == 'input':
        try:
            sp = authorize()
            genre_text = predict_genre(args)
            if verbose > 0:
                print("Genres:", genre_text)
            params = generate_params(args, num_playlists=2, verbose=verbose)
            if verbose > 0:
                print("Spotify params:", params)
            tracks = recommend(params, genre_text, sp, args)
            if verbose > 0:
                print("Playlist (Song URIs):", tracks)
            playlist_url = create_spotify_playlist(tracks, args.text, sp, args)
            if verbose > 0:
                print("Playlist URL:", playlist_url)
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


if __name__ == '__main__':
    main(verbose=0)
