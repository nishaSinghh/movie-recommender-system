import requests
from pprint import pprint

movie_title = "Avatar"
url = f"http://www.omdbapi.com/?t={movie_title}&apikey=c853b243"
response = requests.get(url)
data = response.json()
print(type(data))
print(data)