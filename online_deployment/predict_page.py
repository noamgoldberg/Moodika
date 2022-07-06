import streamlit as st
import pickle
import numpy as np
import argparse
import json
import sys
from urllib.parse import urlencode
import requests
import pandas as pd
import glob
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
from pprint import pprint
from time import sleep
from tqdm import tqdm
import pickle
from sentence_transformers import SentenceTransformer
import config as cfg
import torch
import numpy as np
import xgboost
import pymysql.cursors
import time


def predict_genre(genre_text2, input_text):
    """
    Takes given free text and returns the most similar genres over a given similarity threshold (limit 5).
    Threshold can be configured in config file.
    If no genres are found over similarity threshold, a default list of genres is returned (can be configured as well).
    """

    if genre_text2 == "automatic":
        with open('CrossEncoder_GenrePicker.pkl', 'rb') as ce_file:
            similarity_model = pickle.load(ce_file)

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
            print("{:.2f}\t{}".format(similarity_scores[idx], genres[idx]))
            # if similarity_scores[idx] > cfg.THRESHOLD:
            if len(top_genres) < 5:
                top_genres.append(genres[idx])
                top_scores.append(similarity_scores[idx])

        for i in range(len(top_scores) - 1):
            print(abs(top_scores[i + 1]) - abs(top_scores[i]))
            if abs(top_scores[i + 1]) - abs(top_scores[i]) > 2:
                top_genres = top_genres[:i + 1]
                break

        genre_text2 = top_genres
        print(genre_text2, "auto")

    else:
        genre_text2 = [genre_text2]

    print(genre_text2, "manual")

    return genre_text2


def generate_playlist(input_text, genre_text3, length, popularity):
    # print(input_text, genre_text3, length, popularity)
    AUTH_RESPONSE = requests.post(cfg.AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': cfg.CLIENT_ID,
        'client_secret': cfg.CLIENT_SECRET})

    # convert the response to JSON
    AUTH_RESPONSE_DATA = AUTH_RESPONSE.json()

    # save the access token
    ACCESS_TOKEN = AUTH_RESPONSE_DATA['access_token']

    HEADERS = {'Authorization': 'Bearer {token}'.format(token=ACCESS_TOKEN)}

    with open('MiniLMTransformer.pkl', 'rb') as f:
        transformer_model = pickle.load(f)

    transformers = os.path.join("transformer_xgb_models/*_model_xgb_384")
    transformer_files = glob.glob(transformers)

    input_to_model = transformer_model.encode(input_text)
    parameters = ['target_acousticness', 'target_danceability', 'target_energy', 'target_instrumentalness', 'key',
                  'target_liveness', 'target_loudness', 'mode', 'target_speechiness', 'target_tempo',
                  'time_signature', 'target_valence']
    input_to_spotify_transformer = {'limit': length,
                                    'popularity': popularity}

    for parameter, model in zip(parameters, transformer_files):
        with open(model, 'rb') as f:
            xgb_model = pickle.load(f)
        preds = xgb_model.predict(input_to_model.reshape(1, -1))
        input_to_spotify_transformer[parameter] = preds[0]

    scope = "user-read-playback-state,user-modify-playback-state,playlist-modify-public"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cfg.CLIENT_ID,
                                                   client_secret=cfg.CLIENT_SECRET,
                                                   redirect_uri=cfg.REDIRECT_URI,
                                                   scope=scope))

    result = sp.recommendations(seed_genres=genre_text3, **input_to_spotify_transformer)

    if result:
        track_uris = []
        for track in result['tracks']:
            track_uris.append(track['uri'])
    else:
        raise Exception("Nothing returned from Spotify.")

    print(input_to_spotify_transformer)
    print(track_uris)
    user_id = sp.me()['id']
    playlist_to_add = f"{input_text} - Moodika-generated"

    # Create playlist
    sp.user_playlist_create(user_id, playlist_to_add)
    playlists = sp.user_playlists(user_id)
    playlist_uid = playlists['items'][0]['id']

    generated_playlist = f"https://open.spotify.com/playlist/{playlist_uid}"

    # Add tracks
    sp.playlist_add_items(playlist_uid, track_uris)
    print(generated_playlist)

    return generated_playlist, track_uris, genre_text3


def show_predict_page():
    # st.title("WELCOME TO MOODIKA")
    st.image("moodika.png")

    # st.write("""### Please fill in the below information to get your Playlist!""")

    # st.text_input

    genre = (
        "automatic", "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime", "black-metal", "bluegrass",
        "blues",
        "bossanova", "brazil", "breakbeat", "british", "cantopop", "chicago-house", "children", "chill", "classical",
        "club", "comedy", "country", "dance", "dancehall", "death-metal", "deep-house", "detroit-techno", "disco",
        "disney", "drum-and-bass", "dub", "dubstep", "edm", "electro", "electronic", "emo", "folk", "forro", "french",
        "funk", "garage", "german", "gospel", "goth", "grindcore", "groove", "grunge", "guitar", "happy", "hard-rock",
        "hardcore", "hardstyle", "heavy-metal", "hip-hop", "holidays", "honky-tonk", "house", "idm", "indian", "indie",
        "indie-pop", "industrial", "iranian", "j-dance", "j-idol", "j-pop", "j-rock", "jazz", "k-pop", "kids", "latin",
        "latino", "malay", "mandopop", "metal", "metal-misc", "metalcore", "minimal-techno", "movies", "mpb", "new-age",
        "new-release", "opera", "pagode", "party", "philippines-opm", "piano", "pop", "pop-film", "post-dubstep",
        "power-pop", "progressive-house", "psych-rock", "punk", "punk-rock", "r-n-b", "rainy-day", "reggae",
        "reggaeton", "road-trip", "rock", "rock-n-roll", "rockabilly", "romance", "sad", "salsa", "samba", "sertanejo",
        "show-tunes", "singer-songwriter", "ska", "sleep", "songwriter", "soul", "soundtracks", "spanish", "study",
        "summer", "swedish", "synth-pop", "tango", "techno", "trance", "trip-hop", "turkish", "work-out", "world-music"
    )

    input_text = st.text_input("What are you in the mood for?")

    expander2 = st.expander("Optional parameters")
    ok = st.button("Generate a playlist")
    t = st.empty()

    with expander2:

        # lst = cfg.genres
        # lst = lst.append("automatic")
        genre_text = st.selectbox("Genre?", genre)

        popularity = st.slider("How popular do you want the tracks to be?", 0, 100, 75)
        length = st.slider("How many tracks?", 0, 100, 20)

    a = length
    b = length // 2
    user = st.text_input("Your Name")
    rank = st.slider("How many songs in the playlist were relevant to your input?", 0, a, b)
    model_num = 1
    ok2 = st.button("Submit")

    st.session_state.count = 0
    i = 0

    if ok or st.session_state.count != 0 or i > 0:
        i += 1
        st.session_state.count += 1

        print(input_text)
        genre4 = predict_genre(genre_text, input_text)

        generated_playlist, track_uris, genre_text3 = generate_playlist(input_text, genre4, length,
                                                                        popularity)
        generated_link = f"#### (1) Click [here]({generated_playlist}) to view the playlist \n #### (2) Tell us how much you liked it!"
        t.markdown(generated_link)

        st.experimental_set_query_params(generated_playlist=generated_playlist, track_uris=list(
            map(lambda x: x.replace('spotify:track:', ''), track_uris)), genre_text3=genre_text3)  # Save value

    if ok2:
        app_state = st.experimental_get_query_params()

        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password=PASSWORD,
                                     db=DB,
                                     port=PORT,
                                     cursorclass=pymysql.cursors.DictCursor
                                     )

        sql = "INSERT INTO moodika.rank (rankcol, user, text, playlist_link, genre,popularity,tracks_number,tracks_uris,model,genre_list) VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s)"
        val = (rank, user, input_text, app_state["generated_playlist"], genre_text, popularity, length,
               f"{app_state['track_uris']}", model_num, f'{app_state["genre_text3"]}')

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, val)
                connection.commit()

        st.write("""Thanks for your feedback!""")
        st.balloons()
