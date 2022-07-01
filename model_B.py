import argparse
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
from recommend_playlist import recommend
from recommend_playlist import create_spotify_playlist
import logging

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


def generate_params(model_input, args):
    """
    Takes vector space of dimension 384 and outputs a prediction for each of 12 audio parameters
    using 12 separate pre-trained XGBoostRegressor models.
    Returns a dictionary of predicted parameters, including desired genre and playlist length.
    """
    # Parameters and genre
    genre_text = args.genre
    parameters = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'key',
                  'liveness', 'loudness', 'mode', 'speechiness', 'tempo',
                  'time_signature', 'valence']

    # Create dictionary to be added to
    input_to_spotify_transformer = {'seed_genres': genre_text,
                                    'limit': args.length,
                                    'popularity': args.popularity}

    # Find the XGB files
    xgboost_files = os.path.join("transformer_xgb_models/*_model_xgb_384")
    xgboost_models = glob.glob(xgboost_files)

    # Use each XGB model to predict on corresponding audio parameter
    for parameter, model in zip(parameters, xgboost_models):
        with open(model, 'rb') as f:
            xgb_model = pickle.load(f)
        preds = xgb_model.predict(model_input.reshape(1, -1))
        input_to_spotify_transformer[parameter] = preds[0]

    return input_to_spotify_transformer


def parse_args(args_string_list):
    """
    Parses input arguments.
    Returns a structure with all the input arguments
    """
    # Interface definition
    parser = argparse.ArgumentParser(description="Input your mood to generate spotify playlist.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    subparser = parser.add_subparsers(dest='command')

    login = subparser.add_parser('login', help=f'Update client information. "login -h" for more information')
    login.add_argument('--id', type=str, required=False)
    login.add_argument('--secret', type=str, required=False)

    update = subparser.add_parser('input', help=f'Input to pass to model. "input -h" for more information')
    update.add_argument('-t', '--text', type=str, help='Input text')
    update.add_argument('-g', '--genre', type=str, required=True,
                        help=f'Seed genre to generate from - List: {cfg.genres}')
    update.add_argument('-p', '--popularity', type=int, required=False, help=f'Desired popularity', default=100)
    update.add_argument('-l', '--length', type=int, required=False, help=f'Desired length of playlist', default=100)

    return parser.parse_args(args_string_list)


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
            embedded_text = embed_text(args)
            params = generate_params(embedded_text, args)
            tracks = recommend(params)
            create_spotify_playlist(tracks, args.text)
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
