import os
import pickle
import re
import subprocess

import matplotlib as mpl
import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from PIL import Image
from sklearn.feature_extraction.text import CountVectorizer
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from wordcloud import WordCloud

nltk.download(["punkt", "wordnet", "averaged_perceptron_tagger", "universal_tagset"])

# Create a custom plotly theme and set it as default
pio.templates["custom"] = pio.templates["plotly_white"]
pio.templates["custom"].layout.margin = {"b": 25, "l": 25, "r": 25, "t": 50}
pio.templates["custom"].layout.width = 600
pio.templates["custom"].layout.height = 450
pio.templates["custom"].layout.autosize = False
pio.templates["custom"].layout.font.update(
    {"family": "Arial", "size": 12, "color": "#707070"}
)
pio.templates["custom"].layout.title.update(
    {
        "xref": "container",
        "yref": "container",
        "x": 0.5,
        "yanchor": "top",
        "font_size": 16,
        "y": 0.95,
        "font_color": "#353535",
    }
)
pio.templates["custom"].layout.xaxis.update(
    {"showline": True, "linecolor": "lightgray", "title_font_size": 14}
)
pio.templates["custom"].layout.yaxis.update(
    {"showline": True, "linecolor": "lightgray", "title_font_size": 14}
)
pio.templates["custom"].layout.colorway = [
    "#1F77B4",
    "#FF7F0E",
    "#54A24B",
    "#D62728",
    "#C355FA",
    "#8C564B",
    "#E377C2",
    "#7F7F7F",
    "#FFE323",
    "#17BECF",
]
pio.templates.default = "custom"


def get_latest_tweet_df(search_term, num_tweets, twitter_auth_token):
    # Append the language filter to the search term
    search_keyword = f"{search_term} lang:en"

    # Run tweet-harvest using npx to get the tweets
    try:
        result = subprocess.run(
            [
                "npx",
                "tweet-harvest@2.6.0",
                "-s",
                search_keyword,
                "--tab",
                "LATEST",
                "-l",
                str(num_tweets),
                "--token",
                twitter_auth_token,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print("Error: Command failed with exit status", e.returncode)
        print("Command output:", e.output)
        print("Error output:", e.stderr)
        raise e
    except FileNotFoundError as e:
        print("Error: Ensure that npx is installed and available in your PATH.")
        raise e

    # Find the latest CSV file in the tweets-data directory
    tweets_data_dir = "./tweets-data"
    files = [f for f in os.listdir(tweets_data_dir) if f.endswith(".csv")]
    latest_file = max(
        files, key=lambda f: os.path.getmtime(os.path.join(tweets_data_dir, f))
    )

    # Read the latest CSV file into a pandas DataFrame
    csv_file_path = os.path.join(tweets_data_dir, latest_file)
    tweet_df = pd.read_csv(csv_file_path)

    # Rename columns as needed
    tweet_df = tweet_df.rename(
        columns={
            "created_at": "created_at",
            "full_text": "full_text",
            "reply_count": "reply_count",
            "username": "username",
        }
    )

    return tweet_df


def text_preprocessing(text):
    stopwords = set()
    with open("assets/en_stopwords.txt", "r") as file:
        for word in file:
            stopwords.add(word.rstrip("\n"))
    lemmatizer = WordNetLemmatizer()
    try:
        url_pattern = r"((http://)[^ ]*|(https://)[^ ]*|(www\.)[^ ]*)"
        user_pattern = r"@[^\s]+"
        entity_pattern = r"&.*;"
        neg_contraction = r"n't\W"
        non_alpha = "[^a-z]"
        cleaned_text = text.lower()
        cleaned_text = re.sub(neg_contraction, " not ", cleaned_text)
        cleaned_text = re.sub(url_pattern, " ", cleaned_text)
        cleaned_text = re.sub(user_pattern, " ", cleaned_text)
        cleaned_text = re.sub(entity_pattern, " ", cleaned_text)
        cleaned_text = re.sub(non_alpha, " ", cleaned_text)
        tokens = word_tokenize(cleaned_text)
        word_tag_tuples = pos_tag(tokens, tagset="universal")
        tag_dict = {"NOUN": "n", "VERB": "v", "ADJ": "a", "ADV": "r"}
        final_tokens = []
        for word, tag in word_tag_tuples:
            if len(word) > 1 and word not in stopwords:
                if tag in tag_dict:
                    final_tokens.append(lemmatizer.lemmatize(word, tag_dict[tag]))
                else:
                    final_tokens.append(lemmatizer.lemmatize(word))
        return " ".join(final_tokens)
    except:
        return np.nan


def predict_sentiment(tweet_df):
    model = load_model("assets/model_lstm.h5")
    with open("assets/tokenizer.pickle", "rb") as handle:
        custom_tokenizer = pickle.load(handle)
    temp_df = tweet_df.copy()
    temp_df["Cleaned Tweet"] = temp_df["full_text"].apply(text_preprocessing)
    temp_df = temp_df[
        (temp_df["Cleaned Tweet"].notna()) & (temp_df["Cleaned Tweet"] != "")
    ]
    sequences = pad_sequences(
        custom_tokenizer.texts_to_sequences(temp_df["Cleaned Tweet"]), maxlen=54
    )
    score = model.predict(sequences)
    temp_df["Score"] = score
    temp_df["Sentiment"] = temp_df["Score"].apply(
        lambda x: "Positive" if x >= 0.50 else "Negative"
    )
    return temp_df


def plot_sentiment(tweet_df):
    sentiment_count = tweet_df["Sentiment"].value_counts()
    fig = px.pie(
        values=sentiment_count.values,
        names=sentiment_count.index,
        hole=0.3,
        title="<b>Sentiment Distribution</b>",
        color=sentiment_count.index,
        color_discrete_map={"Positive": "#1F77B4", "Negative": "#FF7F0E"},
    )
    fig.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>%{value} (%{percent})",
        hovertemplate="<b>%{label}</b><br>Percentage=%{percent}<br>Count=%{value}",
    )
    fig.update_layout(showlegend=False)
    return fig


def plot_wordcloud(tweet_df, colormap="Greens"):
    stopwords = set()
    with open("assets/en_stopwords_viz.txt", "r") as file:
        for word in file:
            stopwords.add(word.rstrip("\n"))
    cmap = mpl.cm.get_cmap(colormap)(np.linspace(0, 1, 20))
    cmap = mpl.colors.ListedColormap(cmap[10:15])
    mask = np.array(Image.open("assets/twitter_mask.png"))
    font = "assets/quartzo.ttf"
    text = " ".join(tweet_df["Cleaned Tweet"])
    wc = WordCloud(
        background_color="white",
        font_path=font,
        stopwords=stopwords,
        max_words=90,
        colormap=cmap,
        mask=mask,
        random_state=42,
        collocations=False,
        min_word_length=2,
        max_font_size=200,
    )
    wc.generate(text)
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(1, 1, 1)
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("Wordcloud", fontdict={"fontsize": 16}, fontweight="heavy", pad=20, y=1.0)
    return fig


def get_top_n_gram(tweet_df, ngram_range, n=10):
    stopwords = set()
    with open("assets/en_stopwords_viz.txt", "r") as file:
        for word in file:
            stopwords.add(word.rstrip("\n"))
    stopwords = list(stopwords)
    corpus = tweet_df["Cleaned Tweet"]
    vectorizer = CountVectorizer(
        analyzer="word", ngram_range=ngram_range, stop_words=stopwords
    )
    X = vectorizer.fit_transform(corpus.astype(str).values)
    words = vectorizer.get_feature_names_out()
    words_count = np.ravel(X.sum(axis=0))
    df = pd.DataFrame(zip(words, words_count))
    df.columns = ["words", "counts"]
    df = df.sort_values(by="counts", ascending=False).head(n)
    df["words"] = df["words"].str.title()
    return df


def plot_n_gram(n_gram_df, title, color="#54A24B"):
    fig = px.bar(
        x=n_gram_df.counts,
        y=n_gram_df.words,
        title="<b>{}</b>".format(title),
        text_auto=True,
    )
    fig.update_layout(plot_bgcolor="white")
    fig.update_xaxes(title=None)
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_traces(hovertemplate="<b>%{y}</b><br>Count=%{x}", marker_color=color)
    return fig
