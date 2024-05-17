import streamlit as st

import helper_functions as hf

st.set_page_config(
    page_title="Twitter Sentiment Analyzer", page_icon="📊", layout="wide"
)

# Custom CSS for the toast notification
toast_css = """
<style>
#toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    width: 300px;
    z-index: 10000;
}
.toast {
    display: flex;
    align-items: center;
    padding: 10px;
    background-color: #4BB543;
    color: white;
    border-radius: 5px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
.toast-icon {
    margin-right: 10px;
}
.toast-close {
    margin-left: auto;
    cursor: pointer;
}
</style>
"""

# JavaScript to show the toast notification
toast_js = """
<script>
function showToast(message, icon) {
    var toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.innerHTML = `
        <div class="toast">
            <span class="toast-icon">${icon}</span>
            <span>${message}</span>
            <span class="toast-close" onclick="this.parentElement.style.display='none'">&times;</span>
        </div>
    `;
    document.body.appendChild(toastContainer);
    setTimeout(function() {
        toastContainer.style.display = 'none';
    }, 5000);
}
</script>
"""

# Add custom CSS and JS to the Streamlit app
st.markdown(toast_css, unsafe_allow_html=True)
st.markdown(toast_js, unsafe_allow_html=True)

adjust_top_pad = """
<style>
    div.block-container {padding-top:1rem;}
</style>
"""
st.markdown(adjust_top_pad, unsafe_allow_html=True)


# Whenever the search button is clicked, the search_callback function is called
def search_callback():
    st.session_state.df = hf.get_latest_tweet_df(
        st.session_state.search_term,
        st.session_state.num_tweets,
        st.session_state.twitter_auth_token,
    )
    st.session_state.df = hf.predict_sentiment(st.session_state.df)
    st.session_state.dashboard_ready = True


with st.sidebar:
    st.title("Stream-search Sentiment Analyzer")

    st.markdown(
        """
        <div style="text-align: justify; margin-bottom: 20px;">
            Currently, <strong>only English tweets are supported.</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(key="search_form"):
        st.subheader("Search Parameters")
        st.text_input("Search term", key="search_term")
        st.slider("Number of tweets", min_value=100, max_value=2000, key="num_tweets")
        st.text_input(
            "Enter Twitter Auth Token", key="twitter_auth_token", type="password"
        )
        st.form_submit_button(label="Search", on_click=search_callback)
        st.markdown(
            "Note: Proses Inference mungkin akan memakan waktu, tergantung pada jumlah tweet yang diambil."
        )

if "df" in st.session_state:

    def make_dashboard(tweet_df, bar_color, wc_color, show_wordcloud=True):
        # first row
        col1, col2, col3 = st.columns([28, 34, 38])
        with col1:
            sentiment_plot = hf.plot_sentiment(tweet_df)
            sentiment_plot.update_layout(height=350, title_x=0.5)
            st.plotly_chart(sentiment_plot, theme=None, use_container_width=True)
        with col2:
            top_unigram = hf.get_top_n_gram(tweet_df, ngram_range=(1, 1), n=10)
            unigram_plot = hf.plot_n_gram(
                top_unigram, title="Top 10 Occurring Words", color=bar_color
            )
            unigram_plot.update_layout(height=350)
            st.plotly_chart(unigram_plot, theme=None, use_container_width=True)
        with col3:
            top_bigram = hf.get_top_n_gram(tweet_df, ngram_range=(2, 2), n=10)
            bigram_plot = hf.plot_n_gram(
                top_bigram, title="Top 10 Occurring Bigrams", color=bar_color
            )
            bigram_plot.update_layout(height=350)
            st.plotly_chart(bigram_plot, theme=None, use_container_width=True)

        # second row
        col1, col2 = st.columns([60, 40])
        with col1:

            def sentiment_color(sentiment):
                if sentiment == "Positive":
                    return "background-color: #1F77B4; color: white"
                else:
                    return "background-color: #FF7F0E"

            st.dataframe(
                tweet_df[["Sentiment", "full_text"]].style.applymap(
                    sentiment_color, subset=["Sentiment"]
                ),
                height=350,
            )
        if show_wordcloud:
            with col2:
                wordcloud = hf.plot_wordcloud(tweet_df, colormap=wc_color)
                st.pyplot(wordcloud)

    adjust_tab_font = """
    <style>
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
        font-size: 20px;
    }
    </style>
    """

    st.write(adjust_tab_font, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["All", "Positive 😊", "Negative ☹️"])
    with tab1:
        tweet_df = st.session_state.df
        make_dashboard(tweet_df, bar_color="#54A24B", wc_color="Greens")
    with tab2:
        tweet_df = st.session_state.df.query("Sentiment == 'Positive'")
        make_dashboard(
            tweet_df, bar_color="#1F77B4", wc_color="Blues", show_wordcloud=True
        )
    with tab3:
        tweet_df = st.session_state.df.query("Sentiment == 'Negative'")
        make_dashboard(
            tweet_df, bar_color="#FF7F0E", wc_color="Oranges", show_wordcloud=True
        )

    # Show toast notification
    st.write(
        '<script>showToast("Enjoy the Dashboard", "🎉")</script>',
        unsafe_allow_html=True,
    )
