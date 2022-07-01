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
from recommend_playlist import recommend
from recommend_playlist import create_spotify_playlist


def generate_playlist(args):
    with open('MiniLMTransformer.pkl', 'rb') as f:
        transformer_model = pickle.load(f)

    transformers = os.path.join("transformer_xgb_models/*_model_xgb_384")
    transformer_files = glob.glob(transformers)

    # EMBEDDING - SENTENCE TRANSFORMER MODEL
    input_text = args.text
    genre_text = args.genre
    #genres = genre_text.split()
    input_to_model = transformer_model.encode(input_text)
    parameters = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'key',
                  'liveness', 'loudness', 'mode', 'speechiness', 'tempo',
                  'time_signature', 'valence']
    input_to_spotify_transformer = {'seed_genres': genre_text,
                                    'limit': args.length,
                                    'popularity': args.popularity}

    for parameter, model in zip(parameters, transformer_files):
        with open(model, 'rb') as f:
            xgb_model = pickle.load(f)
        preds = xgb_model.predict(input_to_model.reshape(1, -1))
        input_to_spotify_transformer[parameter] = preds[0]

    tracks = recommend(input_to_spotify_transformer)
    create_spotify_playlist(tracks, args.text)


def parse_args(args_string_list):
    """
    parse_args() is parsing the py file input arguments into the struct args
    :param args_string_list: a list of the input arguments of the py file
    :return a Struct with all the input arguments of the py file
    """
    # logging.debug(f"parse_args() started")

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
    main() getting the input arguments of the py file and calling scrape() with them
    main() also catches exceptions
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
            generate_playlist(args)
        except ValueError as e:
            print(e)
            #logging.critical(e)
        except AttributeError as e:
            print(e)
            #logging.critical(e)
        except TypeError as e:
            print(e)
            #logging.critical(e)


if __name__ == '__main__':
    main()
