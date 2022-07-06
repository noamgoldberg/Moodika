import config as cfg
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
import pickle
import numpy as np

logging.basicConfig(filename=cfg.LOGFILE_NAME, format="%(asctime)s %(levelname)s: %(message)s",
                    level=logging.INFO)


def authorize():
    """
    Create and return a Spotipy instance
    """
    # Define the permissions scope of current user
    scope = "user-read-playback-state,user-modify-playback-state,playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cfg.CLIENT_ID,
                                                   client_secret=cfg.CLIENT_SECRET,
                                                   redirect_uri=cfg.REDIRECT_URI,
                                                   scope=scope))
    return sp


def predict_genre(args):
    """
    Takes given free text and returns the most similar genres over a given similarity threshold (limit 5).
    Threshold can be configured in config file.
    If no genres are found over similarity threshold, a default list of genres is returned (can be configured as well).
    """
    with open('CrossEncoder_GenrePicker.pkl', 'rb') as ce_file:
        similarity_model = pickle.load(ce_file)

    # We want to compute the similarity between the query sentence
    input_text = args.text

    # Take all combinations of the text and genre
    genres = cfg.genres
    sentence_combinations = [[input_text, genre] for genre in genres]

    # find the similarity scores between the text and each genre, and sort from highest to lowest
    similarity_scores = similarity_model.predict(sentence_combinations)
    sim_scores_sorted = reversed(np.argsort(similarity_scores))

    # Return the top genres over a given threshold
    top_genres = []
    top_scores = []
    for idx in sim_scores_sorted:
        if args.verbose > 2:
            print("{:.2f}\t{}".format(similarity_scores[idx], genres[idx]))
        if len(top_genres) < 5:
            top_genres.append(genres[idx])
            top_scores.append(similarity_scores[idx])

    for i in range(len(top_scores) - 1):
        if abs(top_scores[i + 1]) - abs(top_scores[i]) > 2:
            top_genres = top_genres[:i + 1]
            break

    # take only the top 5 genres
    if args.verbose > 0:
        print(f"Genres to be passed to Spotify: {top_genres}")
    return top_genres


def recommend(param_dict, genre_list, sp, args):
    """
    Takes a dictionary of values for various audio parameters and returns a list of Spotify-recommended track URIs.
    """
    # Send a request to Spotify API using Spotipy
    result = sp.recommendations(seed_genres=genre_list, limit=args.length, **param_dict)

    # Iterate over response from Spotify, taking track URIs from recommended tracks
    if result:
        track_uris = []
        if args.verbose > 0:
            print('Playlist')
        for track in result['tracks']:
            if args.verbose > 0:
                print(f"Song: {track['name']}, Artist: {dict(track['album']['artists'][0])['name']}\n")
            track_uris.append(track['uri'])
    else:
        logging.warning(f"Nothing was returned from Spotify for url {param_dict}.")
        raise Exception("Nothing returned from Spotify.")
    return track_uris


def create_spotify_playlist(track_uris, input_text, sp, args):
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
    if args.verbose > 1:
        print(f"Track URIs: {track_uris}")

    # Add tracks
    sp.playlist_add_items(playlist_uid, track_uris)
    logging.info(f"Spotify playlist '{playlist_to_add}' was created for Spotify user '{user_id}'.")

    if args.verbose > 1:
        print(f"User ID: {user_id}")
        print(f"Playlist name: {playlist_to_add}")
    if args.verbose > 0:
        print(playlist_link)
    return playlist_link
