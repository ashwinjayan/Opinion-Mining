from flask import Flask, render_template, request, redirect, url_for
from arango import ArangoClient
from TwitterSearch import *
from textblob import TextBlob,Blobber
from textblob.sentiments import NaiveBayesAnalyzer
from textblob.classifiers import NaiveBayesClassifier
import matplotlib.pyplot as plt
import numpy as np
import json

app = Flask(__name__)
name = []

client = ArangoClient(
    protocol='http',
    host='localhost',
    port=8529,
    username='root',
    password='',
    enable_logging=True
)
ts = TwitterSearch(
    consumer_key = 'VHel5CM9rSCTiGq5nLnjjFpXl',
    consumer_secret = '9PxTWp3jV9AGhf4zz8WqLAKcHCeEjvpZJK5yrnns7yLy9dg04o',
    access_token = '786091085374296068-eRhsClkYYMO8xzVWyUkHqIKXznTQfTc',
    access_token_secret = 'WeUNIWKsMMEChRbn6kKfEA2vlHDGND5v40hIT5X6AGmPt'
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/adminlogin")
def admin_login():
    return render_template("adminlogin.html")


@app.route("/search_results/tweets", methods = ['POST','GET'])
def tweets():

    global name
    global s
    global db
    global c

    #if not 'searchkey' in session:
    if request.method == 'POST' :
        name = request.form['searchkey'].split()
        db = client.db('app')
        c = "".join(name)
    #tweets from twitter is added to the database, retrieval and display to page
    #session[]
    if c !='':
        try:
            s = db.create_collection(c)
        except Exception as e:
            s = db.collection(c)
        try:
            tso = TwitterSearchOrder() # create a TwitterSearchOrder object
            tso.set_keywords(name) # let's define all words we would like to have a look for
            tso.set_language('en') # we want to see english tweets only
            tso.set_count(50)
            tso.set_include_entities(False) # and don't give us all those entity information
            for tweet in ts.search_tweets_iterable(tso):
                tweet_count = ts.get_statistics()[1]
                if tweet_count <= 100 :
                    data1 = tweet['user']['screen_name']
                    data2 = tweet['text']
                    data3 = tweet['user']['followers_count']
                    s.insert({'name' : data1 , 'tweet' : data2, 'followers' : data3})
        except TwitterSearchException as e: # take care of all those ugly errors if there are some
            return e

        tweets1=db.aql.execute('FOR s IN ' + c + ' LIMIT 20 RETURN s')
        return render_template("tweets.html", c = c, tweets1 = tweets1)
    else:
        return redirect(url_for("index"))

@app.route("/search_results/charts")
def charts():
    #sentiment polarity calculation
    global s
    global t
    global v
    global s_blog
    global t_blog
    global v_blog
    s = 0
    t = 0
    v = 0
    s_blog = 0
    t_blog = 0
    v_blog = 0
    tb = Blobber(analyzer=NaiveBayesAnalyzer())
    tweets1 = db.aql.execute('FOR s IN ' + c + ' RETURN s')

    for line in tweets1:
        try:
            #Read in one line of the file, convert it into a json object
            x = tb(line['tweet'])
            if x.sentiment.p_pos > 0.55 :
                s = s + x.sentiment.p_pos
            elif x.sentiment.p_neg > 0.55 :
                t = t + x.sentiment.p_neg
            else :
                v = v + ((x.sentiment.p_pos + x.sentiment.p_neg) / 2.0)

            if line['followers'] > 20000:
                if x.sentiment.p_pos > 0.55 :
                    s_blog = s_blog + x.sentiment.p_pos
                elif x.sentiment.p_neg > 0.55 :
                    t_blog = t_blog + x.sentiment.p_neg
                else :
                    v_blog = v_blog + ((x.sentiment.p_pos + x.sentiment.p_neg) / 2.0)

        except Exception as e:
            print(e)

    p = round(s/(s+t+v)*100)
    neg = round(t/(s+t+v)*100)
    neu = round(v/(s+t+v)*100)
    p_blog = round(s_blog/(s_blog+t_blog+v_blog)*100)
    neg_blog = round(t_blog/(s_blog+t_blog+v_blog)*100)
    neu_blog = round(v_blog/(s_blog+t_blog+v_blog)*100)

    if c != '':
        return render_template("charts.html", c = c, p = p, neg = neg, neu = neu, p_blog = p_blog, neg_blog = neg_blog, neu_blog = neu_blog)
    else:
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug = True)
