import pandas as pd
import tweepy

# Masukkan kunci API Anda di sini
bearer_token = "YOUR_OWN_BEARER_TOKEN"

# Mengautentikasi ke Twitter API
client = tweepy.Client(bearer_token=bearer_token)

# Mengumpulkan tweet berdasarkan hashtag
query = "#archiveteam -is:retweet lang:en"
max_results = 100

tweets = client.search_recent_tweets(
    query=query,
    max_results=max_results,
    tweet_fields=["created_at", "author_id", "text"],
)

# Menyimpan hasil ke dalam list
tweets_list = [[tweet.created_at, tweet.author_id, tweet.text] for tweet in tweets.data]

# Menyimpan hasil ke dalam file CSV
tweets_df = pd.DataFrame(tweets_list, columns=["Datetime", "User ID", "Text"])
tweets_df.to_csv("tweets_v2.csv", index=False)

print("Tweet berhasil dikumpulkan dan disimpan dalam file tweets_v2.csv")
