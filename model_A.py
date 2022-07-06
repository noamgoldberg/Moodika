from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)
import pandas as pd
import sys
import os
from recommend_playlist import *
from config import *
from parse_args import *
import logging


def raise_spotify_error():
    """
    Raise exception if no result is found from Spotify search (should be relatively rare)
    """
    raise Exception(f'Nothing Returned from Spotify. Try using different input.')


def generate_params(args, num_playlists=10):
    """
    Generate parameters from given text.
    Process is as follows:
    1. Search Spotify playlists for given text and return number of playlists given in num_playlists
    2. Return all tracks for each playlist, removing tracks that are of NoneType
    3. Find each audio feature for each song -
        then average for each audio feature across entire playlist for each playlist
    4. Average the averages for each playlist, return a dictionary of average for each audio feature
    """
    # Save text argument and initialize a Spotipy instance
    input_text = args.text
    sp = authorize()

    # (1) Get all playlist uris from playlists in search results
    playlists_results = sp.search(q=input_text, limit=num_playlists, type='playlist')['playlists']
    playlist_uris = [playlist['id'] for playlist in playlists_results['items']]
    if args.verbose > 1:
        print("Playlist URIs (list of strings):", playlist_uris, '\n')

    # (2) Get all track uris from playlists in search results
    track_results = [sp.playlist_items(p_uri, limit=100) for p_uri in playlist_uris]
    if len(track_results) == 0:
        raise_spotify_error()

    # Make sure to remove NoneTypes
    track_uris_dict = {playlist_uris[i]: [track['track']['id'] if track['track'] is not None else None for track in
                                          track_results[i]['items']] for i in range(len(playlist_uris))}
    track_uris_dict = {key: [track_uri for track_uri in track_uris_dict[key] if track_uri] for key in track_uris_dict}
    if args.verbose > 4:
        print("Track URIs (dict):\n", track_uris_dict)

    # (3) Get audio features of each track in each playlist
    audio_features = [sp.audio_features(tracks=track_uris_dict[playlist]) for playlist in track_uris_dict]

    # (4) Average playlist averages to get average audio features for individual search
    audio_features = [[track_features for track_features in playlist if track_features] for playlist in audio_features]
    if args.verbose > 4:
        print("Audio Features (list of ):\n", audio_features)

    # Build dictionary of averages
    audio_features = [[{f: track[f] for f in AUDIO_FEATURES_TO_EXTRACT} for track in playlist] for playlist in
                      audio_features]
    avg_audio_features = dict(pd.concat([pd.DataFrame(audio_features[i]).mean() for i in range(len(playlist_uris))],
                                        axis=1).mean(axis=1))

    # Add popularity given to parameter dictionary
    avg_audio_features['popularity'] = args.popularity
    if args.verbose > 1:
        print("Features averaged (series):\n", avg_audio_features, '\n')
    return avg_audio_features


def main():
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    args = parse_args(sys.argv[1:])
    if args.verbose > 1:
        print("\nParsed args:", args, '\n')
    if args.command == 'input':
        try:
            sp = authorize()
            genre_text = predict_genre(args)
            if args.verbose > 1:
                print("\nGenres:", genre_text, '\n')
            params = generate_params(args, num_playlists=7)
            tracks = recommend(params, genre_text, sp, args)
            if args.verbose > 1:
                print("Playlist (Song URIs):", tracks)
            create_spotify_playlist(tracks, args.text, sp, args)
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
    main()
