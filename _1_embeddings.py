"""
Get tags, weights, and embeddings for a given input phrase
"""
import numpy as np
import os
import nltk
from keybert import KeyBERT
import gensim
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import pickle


def get_input():
    """
    Get input from user
    :return:
    """
    phrase = input("What are you in the mood for? ")
    return phrase


def lemmatize_tags(tags):
    """
    Lemmatize tags (called if lemmatize=True in get_tags_and_weights())
    :param tags: tags from input
    :return: list of lemmatized tags
    """
    nlp = spacy.load('en_core_web_sm')
    return [token.lemma_.lower() for token in nlp(' '.join(tags))]


def get_tags_and_weights(phrase, method='nltk', lemmatize=False):
    """
    Extracts tags & weights for each tag from input phrase
    :param phrase: input phrase (e.g. "Sunset in the summer")
    :param method: 'nltk', 'KeyBERT'
    :param tfidf_weights: if True --> assign tfidf weights to each tag
    :param lemmatize: if True --> lemmatize each tag
    :return tags, weights: tags & weights for each tag
    """
    if method == 'nltk':
        stop_words = set(nltk.corpus.stopwords.words('english'))
        tags = [word.lower() for word in phrase.split() if word not in stop_words]
        weights = [(1 / len(tags)) for t in tags]
        if lemmatize:
            tags = lemmatize_tags(tags)
        return tags, weights
    elif method == 'KeyBERT':
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        keywords_and_weights = KeyBERT().extract_keywords(phrase)
        tags = [kw[0] for kw in keywords_and_weights]
        weights = [kw[1] for kw in keywords_and_weights]
        return tags, weights
    else:
        raise ValueError(f"Invalid input {method}. Use inputs 'nltk' or 'KeyBERT.")


def get_embeddings(tags):
    """
    GENSIM embedding generator for list of tags
    :param tags: tags for to generate embeddings
    :return embeddings: numpy array of GENSIM embeddings for each tag
    """
    # with open('gensim-model.pkl', 'rb') as f:
    #     model = pickle.load(f)
    # ^^^^ code for loading gensim model from .pkl in Jupyter notebook
    model = gensim.models.KeyedVectors.load('Models/gensim-model.pkl')
    embeddings = []
    for tag in tags:
        embeddings += [model[tag]]
    return np.array(embeddings)


def example():
    """
    Example of how to use the above function(s)
    """
    phrase_ex = "Sunset on the beach at a music festival"

    # (1) get_tags_and_weights()
    print("METHOD 1.1: Remove NLTK stop words - even weights")
    tags, weights = get_tags_and_weights(phrase_ex, method='nltk', lemmatize=False)
    print("Tags:", tags)
    print("Weights:", weights)

    print("\nMETHOD 2: KeyBERT - lemmatize, KeyBERT weights")
    tags, weights = get_tags_and_weights(phrase_ex, method='KeyBERT', lemmatize=True)
    print("Tags:", tags)
    print("Weights:", weights)

    # (2) get_tags_and_weights()
    tags = ['summer', 'sunset', 'drive']
    embeddings = get_embeddings(tags)
    for tag in tags:
        print(f"\nTag: {tag}\nEmbedding: {embeddings[0]}")


def main1():
    """
    Called from Model A/B to extract tags, weights, and embeddings
    :return tags: keyword from input phrase
    :return weights: weights for each keyword
    :return embeddings: GENSIM embeddings for each input tag
    """
    phrase = get_input()
    tags, weights = get_tags_and_weights(phrase, method='nltk', tfidf_weights=False, lemmatize=False)
    embeddings = get_embeddings(tags)
    print(tags, weights, embeddings)
    return tags, embeddings, weights


# main1()

if __name__ == '__main__':
    example()
