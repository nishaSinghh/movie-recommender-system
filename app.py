import os
import streamlit as st
import pickle
import requests
import base64
import random

# -----------------------------
# API Helpers
# -----------------------------
def fetch_movie_details(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey=c853b243"
    response = requests.get(url)
    return response.json()

def fetch_poster(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey=c853b243"
    response = requests.get(url)
    data = response.json()
    poster = data.get('Poster', None)
    if poster is None or poster == "N/A":
        poster = "https://via.placeholder.com/300x450?text=No+Image"
    return poster

# -----------------------------
# Popular Movies
# -----------------------------
popular_movies = [
    "Inception", "Interstellar", "Avatar", "Titanic", "The Dark Knight",
    "Avengers: Endgame", "Joker", "Forrest Gump", "Gladiator", "The Matrix"
]

# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(page_title="Movie Recommender", layout="wide")

# -----------------------------
# Session State
# -----------------------------
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "recommended_triggered" not in st.session_state:
    st.session_state.recommended_triggered = False
if "last_selected" not in st.session_state:
    st.session_state.last_selected = None
if "favourites" not in st.session_state:
    st.session_state.favourites = []

# -----------------------------
# Background
# -----------------------------
def get_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg_from_local_image(relative_path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(BASE_DIR, relative_path)

    encoded = get_base64(image_path)
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
    }}
    .main-title {{
        font-size: 48px;
        color: #00adb5;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }}
    .subtext {{
        font-size: 20px;
        text-align: center;
        color: #eeeeee;
        margin-bottom: 40px;
    }}
    .section-title {{
        font-size: 28px;
        color: #f39c12;
        margin: 30px 0 10px 0;
        font-weight: bold;
    }}
    .movie-card {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        margin-bottom: 20px;
        text-align: center;
        background-color: rgba(0,0,0,0.6);
        padding: 10px;
    }}
    .movie-title {{
        color: #ffffff;
        font-weight: bold;
        margin-top: 5px;
        font-size: 16px;
    }}
    .imdb-link {{
        color: #f39c12;
        text-decoration: none;
        font-weight: bold;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_bg_from_local_image("assets/golden-frame-blue-background.jpg")

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="main-title">🎬 Movie Recommender System</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Get the top 5 similar movies based on your choice</div>', unsafe_allow_html=True)

# -----------------------------
# Load Data
# -----------------------------
movies = pickle.load(open('movie.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))
movie_list = movies['original_title'].values

# -----------------------------
# Recommendation Logic
# -----------------------------
def recommend(movie):
    index = movies[movies['original_title'] == movie].index[0]
    distances = similarity[index]
    movie_list_ = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    recommended = []
    for i in movie_list_:
        title = movies.iloc[i[0]].original_title
        poster = fetch_poster(title)
        recommended.append((title, poster))
    return recommended

# -----------------------------
# Show Movie Details
# -----------------------------
def show_movie_details(movie_title):
    data = fetch_movie_details(movie_title)

    st.markdown(f"<div class='movie-card'>"
                f"<img src='{data.get('Poster', '')}' style='width:100%; border-radius:10px;'/>"
                f"<h2 class='movie-title'>{movie_title}</h2>"
                f"<p style='color:#dddddd'><strong>Plot:</strong> {data.get('Plot','N/A')}</p>"
                f"<p style='color:#dddddd'><strong>Director:</strong> {data.get('Director','N/A')}</p>"
                f"<p style='color:#dddddd'><strong>Writers:</strong> {data.get('Writer','N/A')}</p>"
                f"<p style='color:#dddddd'><strong>Stars:</strong> {data.get('Actors','N/A')}</p>"
                f"<a class='imdb-link' href='https://www.imdb.com/title/{data.get('imdbID')}' target='_blank'>🔗 View on IMDb</a>"
                f"</div>", unsafe_allow_html=True)

    # Save to Favourites
    if st.button("💖 Save to Favourites", key=f"fav_{movie_title}"):
        if movie_title not in st.session_state.favourites:
            st.session_state.favourites.append(movie_title)
            st.success(f"'{movie_title}' added to favourites!")
        else:
            st.info(f"'{movie_title}' is already in favourites.")

    st.markdown("---")
    top_trending(exclude_movie=movie_title)

    # Back button
    if st.button("⬅️ Back to Recommendations"):
        st.session_state.selected_movie = None
        st.session_state.recommended_triggered = True
        st.rerun()

# -----------------------------
# Show Favourites
# -----------------------------
def show_favourites():
    st.markdown('<div class="section-title">⭐ Your Favourite Movies</div>', unsafe_allow_html=True)
    
    if not st.session_state.favourites:
        st.info("You have not saved any favourites yet!")
        return

    cols = st.columns(5)
    for idx, title in enumerate(st.session_state.favourites):
        poster = fetch_poster(title)
        with cols[idx % 5]:
            st.image(poster, use_container_width=True)
            st.caption(title)
            if st.button("❌ Remove", key=f"remove_{idx}"):
                st.session_state.favourites.remove(title)
                st.experimental_rerun()

# -----------------------------
# Trending Movies (Clickable)
# -----------------------------
def top_trending(exclude_movie=None):
    st.markdown('<div class="section-title">🔥 You may also like</div>', unsafe_allow_html=True)
    popular = movies.head(100).sample(10, random_state=None)

    if exclude_movie:
        popular = popular[popular['original_title'] != exclude_movie]

    cols = st.columns(5)
    for idx, col in enumerate(cols * 2):
        if idx >= len(popular):
            break
        title = popular.iloc[idx].original_title
        poster = fetch_poster(title)

        with col:
            st.image(poster, use_container_width=True)
            st.caption(title)
            if st.button(f"details_{title}", key=f"trending_{idx}"):
                st.session_state.selected_movie = title
                st.rerun()

# -----------------------------
# Show Recommendations
# -----------------------------
def show_recommendation(movie):
    recommended = recommend(movie)
    st.markdown('<div class="section-title">🎯 Top 5 Recommended Movies</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    for idx, rec in enumerate(recommended):
        title, poster = rec
        with cols[idx]:
            st.image(poster, use_container_width=True)
            st.caption(title)
            if st.button(f"rec_{title}", key=f"rec_btn_{idx}"):
                st.session_state.selected_movie = title
                st.rerun()

# -----------------------------
# Sidebar Favourites Button
# -----------------------------
st.sidebar.title("💖 Favourites")
if st.sidebar.button("Show Favourites"):
    st.session_state.selected_movie = None
    st.session_state.recommended_triggered = False
    show_favourites()

# -----------------------------
# Main Page Logic
# -----------------------------
if st.session_state.selected_movie:
    show_movie_details(st.session_state.selected_movie)

elif st.session_state.recommended_triggered:
    show_recommendation(st.session_state.last_selected)
    top_trending(exclude_movie=st.session_state.last_selected)

else:
    selected_movie_name = st.selectbox("Select a movie", movie_list)
    if st.button("🔍 Recommend Movies"):
        st.session_state.recommended_triggered = True
        st.session_state.last_selected = selected_movie_name
        st.rerun()
    top_trending()

    st.markdown("<h3 style='margin-top: 50px;'>More Popular Movies</h3>", unsafe_allow_html=True)

    # Display Popular Movies (clickable)
    def get_dynamic_images():
        movies_ = []
        for title in popular_movies:
            poster = fetch_poster(title)
            if poster and poster != "N/A":
                movies_.append({"title": title, "poster": poster})
        return movies_
    
    movies_data = get_dynamic_images()
    for i in range(0, len(movies_data), 5):
        cols = st.columns(5)
        for j, movie in enumerate(movies_data[i:i + 5]):
            with cols[j]:
                st.image(movie["poster"], use_container_width=True)
                st.caption(movie["title"])
                if st.button(f"details_{movie['title']}", key=f"popular_{i}_{j}"):
                    st.session_state.selected_movie = movie["title"]
                    st.rerun()

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<hr>
<p style='text-align: center; color: grey;'>
    Made with ❤️ by Nisha | Powered by Streamlit
</p>
""", unsafe_allow_html=True)
