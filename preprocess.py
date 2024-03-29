"""
Preprocess and visualisation
"""
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import json_tricks as json
from collections import OrderedDict
from datetime import datetime
import time
import os
import sys
import multiprocessing
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

pd.set_option('display.max_colwidth', -1)
sns.set(style='darkgrid')

ARTICLES = pd.read_json("dataset/articles.json")

print("ARTICLES.shape: ", ARTICLES.shape)
# print(TWEETS.head())

# print schema
print("Schema:\n", ARTICLES.dtypes)
print("Number of questions,columns=", ARTICLES.shape)

# Join Facebook Data
print(ARTICLES['fb_data'].dtype)
fb_dict = dict(ARTICLES['fb_data'])
fb_df = pd.DataFrame(fb_dict).transpose()
ARTICLES_WITH_FB = ARTICLES.join(fb_df)
# print(ARTICLES_WITH_FB)

# ARTICLES_WITH_FB = pd.concat([ARTICLES, fb_df])
# print(ARTICLES_WITH_FB.head())

# Select fb engagement > 100 OR max velocity > 0.05
ARTICLES_WITH_FB_max_velo_zero_five_plus_OR_fb_one_hundred_plus = ARTICLES_WITH_FB[(ARTICLES_WITH_FB['total_engagement_count'] > 100) | (ARTICLES_WITH_FB['velocity'] > 0.05)]
print(ARTICLES_WITH_FB_max_velo_zero_five_plus_OR_fb_one_hundred_plus.shape)


# Visualisation
plot_velo_fb = sns.scatterplot(x=ARTICLES_WITH_FB['total_engagement_count'], y=ARTICLES_WITH_FB['max_velocity'])
plot_velo_fb.set_title("Max Velocity and FB Engagement")
plot_velo_fb.set_xlabel("total_engagement_count")
plot_velo_fb.set_ylabel("max_velocity")
fig_velo_fb = plot_velo_fb.get_figure()
fig_velo_fb.savefig("Max_Velocity_vs_FB_Engagement.png")

plot_velo_fb_zoom = sns.scatterplot(x=ARTICLES_WITH_FB['total_engagement_count'], y=ARTICLES_WITH_FB['max_velocity'])
plot_velo_fb_zoom.set_title("Max Velocity and FB Engagement")
plot_velo_fb_zoom.set_xlabel("total_engagement_count")
plot_velo_fb_zoom.set_ylabel("max_velocity")
plot_velo_fb_zoom.set_xlim(-500, 20000)
plot_velo_fb_zoom.set_ylim(-250, 4000)
fig_velo_fb_zoom = plot_velo_fb_zoom.get_figure()
fig_velo_fb_zoom.savefig("Max_Velocity_vs_FB_Engagement_zoom.png")

ARTICLES_WITH_FB_max_velo_valid = ARTICLES_WITH_FB_max_velo_zero_five_plus_OR_fb_one_hundred_plus[ARTICLES_WITH_FB_max_velo_zero_five_plus_OR_fb_one_hundred_plus['max_velocity'] > 0]
ARTICLES_WITH_FB_fb_engagement_valid = ARTICLES_WITH_FB_max_velo_zero_five_plus_OR_fb_one_hundred_plus[ARTICLES_WITH_FB_max_velo_zero_five_plus_OR_fb_one_hundred_plus['total_engagement_count'] > 0]

time_plot_velo = sns.scatterplot(x=ARTICLES_WITH_FB_max_velo_valid['publication_timestamp'], y=ARTICLES_WITH_FB_max_velo_valid['max_velocity'])
time_plot_velo.set_title("Max Velocity Over Time")
time_plot_velo.set_xlabel("time")
time_plot_velo.set_xlim(1.47e12, 1.57e12)
time_plot_velo.set_ylabel("Max Velocity")
time_figure_velo = time_plot_velo.get_figure()
time_figure_velo.savefig("Max_Velocity_vs_time.png")

time_plot_fb = sns.scatterplot(x=ARTICLES_WITH_FB_fb_engagement_valid['publication_timestamp'], y=ARTICLES_WITH_FB_fb_engagement_valid['total_engagement_count'])
time_plot_fb.set_title("FB Engagement Over Time")
time_plot_fb.set_xlabel("time")
time_plot_fb.set_xlim(1.47e12, 1.57e12)
time_plot_fb.set_ylabel("FB Engagement")
time_figure_fb = time_plot_fb.get_figure()
time_figure_fb.savefig("FB_Engagement_vs_time.png")

time_plot_velo_zoom = sns.scatterplot(x=ARTICLES_WITH_FB_max_velo_valid['publication_timestamp'], y=ARTICLES_WITH_FB_max_velo_valid['max_velocity'])
time_plot_velo_zoom.set_title("Max Velocity Over Time (Below 4000)")
time_plot_velo_zoom.set_xlabel("time")
time_plot_velo_zoom.set_xlim(1.47e12, 1.57e12)
time_plot_velo_zoom.set_ylim(-100 , 4000)
time_plot_velo_zoom.set_xlabel("time")
time_plot_velo_zoom.set_ylabel("Max Velocity")
time_figure_velo_zoom = time_plot_velo_zoom.get_figure()
time_figure_velo_zoom.savefig("Max_Velocity_vs_time_Below_4k.png")

time_plot_fb_zoom = sns.scatterplot(x=ARTICLES_WITH_FB_fb_engagement_valid['publication_timestamp'], y=ARTICLES_WITH_FB_fb_engagement_valid['total_engagement_count'])
time_plot_fb_zoom.set_title("FB Engagement Over Time (Below 200000)")
time_plot_fb_zoom.set_xlabel("time")
time_plot_fb_zoom.set_xlim(1.47e12, 1.57e12)
time_plot_fb_zoom.set_ylim(-1000, 200000)
time_plot_fb_zoom.set_ylabel("FB Engagement")
time_figure_fb_zoom = time_plot_fb_zoom.get_figure()
time_figure_fb_zoom.savefig("FB_Engagement_vs_time_below_20k.png")


def pre_process(text):
    # lowercase
    text = text.lower()

    # remove tags
    text = re.sub("<!--?.*?-->", "", text)

    # remove special characters and digits
    text = re.sub("(\\d|\\W)+", " ", text)

    return text


ARTICLES_WITH_FB['contents'] = ARTICLES_WITH_FB['contents'].apply(lambda x: pre_process(x))


def get_stop_words(stop_file_path):
    """load stop words """
    with open(stop_file_path, 'r', encoding="utf-8") as f:
        stopwords = f.readlines()
        stop_set = set(m.strip() for m in stopwords)
        return frozenset(stop_set)


# load a set of stop words
# stopwords = get_stop_words("resources/stopwords.txt")

# get the text column
docs = ARTICLES_WITH_FB['contents'].tolist()

# create a vocabulary of words,
# ignore words that appear in 85% of documents,
# eliminate stop words
cv = CountVectorizer(max_df=0.85, stop_words='english')
word_count_vector = cv.fit_transform(docs)

tfidf_transformer=TfidfTransformer(smooth_idf=True, use_idf=True)
tfidf_transformer.fit(word_count_vector)


def sort_coo(coo_matrix):
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)


def extract_topn_from_vector(feature_names, sorted_items, topn=10):
    """get the feature names and tf-idf score of top n items"""

    # use only topn items from vector
    sorted_items = sorted_items[:topn]

    score_vals = []
    feature_vals = []

    # word index and corresponding tf-idf score
    for idx, score in sorted_items:
        # keep track of feature name and its corresponding score
        score_vals.append(round(score, 3))
        feature_vals.append(feature_names[idx])

    # create a tuples of feature,score
    # results = zip(feature_vals,score_vals)
    results = {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]] = score_vals[idx]

    return results


feature_names = cv.get_feature_names()

doc = ''

for i in range(16768):
    # get the document that we want to extract keywords from
    # doc = docs[2]
    doc += docs[i]

    # generate tf-idf for the given document
    tf_idf_vector = tfidf_transformer.transform(cv.transform([doc]))

    # sort the tf-idf vectors by descending order of scores
    sorted_items = sort_coo(tf_idf_vector.tocoo())

    # extract only the top n; n here is 10
    keywords = extract_topn_from_vector(feature_names, sorted_items, 10)

    # now print the results
    print("\n=====Doc=====")
    print(doc)
    print("\n===Keywords===")
    for k in keywords:
        print(k, keywords[k])
