from flask import Flask, render_template, request, url_for
from dotenv import load_dotenv
import os
import base64
from requests import post, get, exceptions
import json
import sys
import pycountry

# Setting our server
app = Flask(__name__)  # "__name__" means : Turn this file into a web application

# Loading environment variables
try:
    load_dotenv()
except ModuleNotFoundError:
    sys.exit("Please install dotenv module before running app.")

# Loading our client ID and secret
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


# Custom Error class inherited from the Exception class which provides a default error message that will be displayed when the exception is raised if no custom message is provided.
class NoResultError(Exception):
    def __init__(self, message="Sorry, no result was obtained after querying the API."):
        super().__init__(message)


class Playlist:
    ### OBJECT INITIALIZATION ###

    def __init__(self, token, country):
        # Instance attributes are protected, because there's no need for them to be accessible by the external user
        self._token = token
        self._country = country
        self._playlist_id = search_for_playlist(token, country)["id"]
        self._playlist_cover_url = search_for_playlist(token, country)["images"][0]["url"]
        self._track_name_and_artist = get_playlist_tracks(token, self._playlist_id)[
            "track_name_and_artist"
        ]  # List of len=20 containing 20 str entries corresponding to the 20 most played tracks in a country
        self._tracks_preview_url = get_playlist_tracks(token, self._playlist_id)["tracks_preview_url"]

    ### GETTER METHODS ###

    @property
    def country(self):
        return self._country

    @property
    def playlist_id(self):
        return self._playlist_id

    @property
    def playlist_cover_url(self):
        return self._playlist_cover_url

    @property
    def track_name_and_artist(self):
        return self._track_name_and_artist

    @property
    def tracks_preview_url(self):
        return self._tracks_preview_url

# GLOBAL SCOPE VARIABLE "all_countries": list of all countries in the world (using list comprehension notation)
all_countries = [country.name.lower() for country in pycountry.countries]
str_countries = ','.join(all_countries) # all_countries list items joined by commas to for a huge str (that will be passed to the html template and further processed on the front via JS)

def main():
    # This token is what we'll need in the future to be pass as a header when making get requests (artists, songs, albums, etc.)
    token = get_token()

    #country input provided by user
    country = request.form["user-input"].lower()

    if country in all_countries:
        return {'playlist': Playlist(token, country), 'str_countries': str_countries} # I could not just simply assign a Python list to a JS array. I had to first joint all list items on the Python side with a comma to form a string and the split them with a comma again on the JS side
    else:
        raise NoResultError("Not a valid country name.")


# Getting the acces token
# We send the Client credentials to the Spotify server and get a temporary access token in return
# Concatenates clientID and clientSecret and encode them with base64
def get_token():
    # b64 encoding
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(
        base64.b64encode(auth_bytes), "utf-8"
    )  # base64.b64encode(auth_bytes) returns a base64object, that we convert in a string to be passed along the header ins the request

    # url that we'll send the requet to
    url = "https://accounts.spotify.com/api/token"

    # headers that we'll be passed along with the authorization string to the url POST request
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)

    if (
        result.status_code == 200
    ):  # Retrieving the token if and only if the post request was sucessful
        json_result = json.loads(result.content)
        token = json_result["access_token"]
        return token
    else:
        raise NoResultError(
            "Invalid access token, check your client credentials encoding and/or request method."
        )


# This function constructs the header we need in order to make a future request
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_playlist(token, country):

    url = "https://api.spotify.com/v1/search"

    new_country = country.lower()
    if new_country in all_countries:
        query = f"q=top50{new_country}&type=playlist&limit=1"
    else:
        raise ValueError

    query_url = url + "?" + query

    result = get(query_url, headers=get_auth_header(token))
    json_result = json.loads(result.content)["playlists"]["items"][
        0
    ]  # json_result is an array containing information on all the playlists found with the query

    if len(json_result) == 0:
        raise NoResultError("No playlist was returned by the query.")
    return {
        "name": json_result["name"],
        "id": json_result["id"],
        "images": json_result["images"],
    }

def get_playlist_tracks(token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"

    try:
        result = get(url, headers=get_auth_header(token))
        result.raise_for_status()  # Raise HTTPError for 4xx or 5xx status codes
    except exceptions.HTTPError as error:
        raise NoResultError(f"HTTP error occured: {error}")


    json_result = json.loads(result.content)["tracks"]["items"]

    if len(json_result) == 0:
        raise NoResultError("This playlist is empty.")
    else:
        track_name_and_artist = []
        tracks_preview_url = []
        # Populating the tracks_list with the title of the 20 most played tracks in the given country
        for i in range(20):
            track_name_and_artist.append(
                json_result[i]["track"]["artists"][0]["name"]
                + " - "
                + json_result[i]["track"]["name"]
            )
            tracks_preview_url.append(json_result[i]["track"]["preview_url"])

    return {
        "track_name_and_artist": track_name_and_artist,
        "tracks_preview_url": tracks_preview_url,
    }  # List of len=20 containing 20 str entries corresponding to the 20 most played tracks in a country


# Flask looks for templates in a folder named templates in the same directory as your main Python script. Make sure that you have created a folder named templates and placed the index.html file inside it.
# This route handles the html input submission from the HTML page whenever a post request's made
@app.route(
    "/", methods=["GET", "POST"]
)  # POST requests are generally used when we don't want the HTTP parameters to be visible on the browser url
def index():
    if request.method == "GET":
        return render_template(
            "index.html", country=None, track_and_url=None, playlist_cover_img_url=None, str_countries=str_countries
        )
    else:
        playlist = main()['playlist']

        # Returning a response to the client's post request. In Flask, each route function should return a response that will be sent back to the client.
        track_name_and_artist = playlist.track_name_and_artist

        tracks_preview_url = playlist.tracks_preview_url

        track_and_url = {
            track: url for track, url in zip(track_name_and_artist, tracks_preview_url)
        }  # Using the zip() function to loop simultaneously over 2 iterables and dict comprehension notation to create a dict object out of those 2 lists.

        return render_template(
            "index.html",
            country = playlist.country,
            str_countries=str_countries,
            track_and_url=track_and_url,
            playlist_cover_url=playlist.playlist_cover_url,
        )


if __name__ == "__main__":
    app.run(debug=True)



