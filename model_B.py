import json
import sys
import pandas as pd
import glob
import os
import pickle
from sentence_transformers import SentenceTransformer
import config as cfg
import torch
import numpy as np
import xgboost
from recommend_playlist import recommend, create_spotify_playlist, authorize
import logging
from parse_args import parse_args

logging.basicConfig(filename=cfg.LOGFILE_NAME, format="%(asctime)s %(levelname)s: %(message)s",
                    level=logging.INFO)


def embed_text(args):
    """
    Uses HuggingFace sentence-transformers/all-MiniLM-L6-v2 model to map sentences & paragraphs 
    to a 384 dimensional dense vector space for use as input to playlist generation model. 
    Returns vector space.
    """
    # Open saved pickle file 
    with open('MiniLMTransformer.pkl', 'rb') as f:
        embedder = pickle.load(f)

    # Embed input text
    input_text = args.text
    input_to_model = embedder.encode(input_text)
    return input_to_model


def predict_genre(args):
    with open('CrossEncoder_GenrePicker.pkl', 'rb') as ce_file:
        similarity_model = pickle.load(ce_file)

    # We want to compute the similarity between the query sentence
    input_text = args.text

    # With all genres
    genres = cfg.genres
    sentence_combinations = [[input_text, genre] for genre in genres]
    similarity_scores = similarity_model.predict(sentence_combinations)
    sim_scores_sorted = reversed(np.argsort(similarity_scores))

    top_genres = []
    for idx in sim_scores_sorted:
        if similarity_scores[idx] > cfg.THRESHOLD:
            top_genres.append(genres[idx])

        print("{:.2f}\t{}".format(similarity_scores[idx], genres[idx]))

    if len(top_genres) == 0:
        top_genres = cfg.default_genres
    print(top_genres)
    genre_text = top_genres[:5]
    return genre_text


def generate_params(model_input, args):
    """
    Takes vector space of dimension 384 and outputs a prediction for each of 12 audio parameters
    using 12 separate pre-trained XGBoostRegressor models.
    Returns a dictionary of predicted parameters, including desired genre and playlist length.
    """
    # Parameters and genre

    parameters = ['target_acousticness', 'target_danceability', 'target_energy', 'target_instrumentalness',
                  'key', 'target_liveness', 'target_loudness', 'mode', 'target_speechiness',
                  'target_tempo', 'time_signature', 'target_valence']

    # Create dictionary to be added to
    input_to_spotify_transformer = {'popularity': args.popularity}

    # Find the XGB files
    xgboost_files = os.path.join("transformer_xgb_models/*_model_xgb_384")
    xgboost_models = glob.glob(xgboost_files)

    # Use each XGB model to predict on corresponding audio parameter
    for parameter, model in zip(parameters, xgboost_models):
        with open(model, 'rb') as f:
            xgb_model = pickle.load(f)
        preds = xgb_model.predict(model_input.reshape(1, -1))
        input_to_spotify_transformer[parameter] = preds[0]

    print(input_to_spotify_transformer)
    return input_to_spotify_transformer


def main():
    """
    Main function, parses the arguments and uses them to create a recommended Spotify playlist on user's account.
    """
    # Get user arguments
    args = parse_args(sys.argv[1:])

    # # Read login information from login.json
    # with open("login.json", "r") as openfile:
    #     login_info = json.load(openfile)
    #
    # # Update user login information for connection
    # if args.command == 'login':
    #     if args.id:
    #         with open("login.json", "w") as outfile:
    #             login_info['hostname'] = args.id
    #             json.dump(login_info, outfile)
    #
    #     if args.secret:
    #         with open("login.json", "w") as outfile:
    #             login_info['username'] = args.username
    #             json.dump(login_info, outfile)
    #
    #     return

    # Run scrape() by user's criteria
    if args.command == 'input':
        try:
            sp = authorize()
            genres = predict_genre(args)
            embedded_text = embed_text(args)
            params = generate_params(embedded_text, args)
            tracks = recommend(params, genres, sp, args)
            create_spotify_playlist(tracks, args.text, sp)
        except ValueError as e:
            print(e)
            logging.critical(e)
        except AttributeError as e:
            print(e)
            logging.critical(e)
        except TypeError as e:
            print(e)
            logging.critical(e)


if __name__ == '__main__':
    main()
