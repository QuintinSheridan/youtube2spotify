'''
-Youtube Data API: https://developers.google.com/youtube/v3
-Spotify Web API: https://developer.spotify.com/documentation/web-api/
-youtube_dl: https://github.com/ytdl-org/youtube-dl
-python requests library: https://requests.readthedocs.io/en/master/
'''

import json
import requests 
from secrets import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import youtube_dl


class CreatePlaylist: 
    def __init__(self):
        self.spotify_id = SPOTIFY_CLIENT_ID
        self.spotify_token = SPOTIFY_CLIENT_SECRET
        self.youtube_client = self.get_youtube_client()
        self.all_song_info  = {}

    # # log into YouTube
    # def get_youtube_client(self):
    #     # from https://developers.google.com/youtube/v3/docs/search/list -> show code -> python
    #     # Sample Python code for youtube.search.list
    #     # See instructions for running these code samples locally:
    #     # https://developers.google.com/explorer-help/guides/code_samples#python
    #     # Disable OAuthlib's HTTPS verification when running locally.
    #     # *DO NOT* leave this option enabled in production.
    #     os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    #     api_service_name = "youtube"
    #     api_version = "v3"
    #     client_secrets_file = "client_secret.json"

    #     # Get credentials and create an API client
    #     scopes = scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    #     flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    #     credentials = flow.run_console()
    #     youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

    #     request = youtube.search().list(
    #         forMine=True,
    #         part="snippet",
    #         type="video"
    #     )
    #     response = request.execute()

    #     print(response)

    def get_youtube_client(self):
        """ Log Into Youtube, Copied from Youtube Data API """
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client
        

    # get liked videos from youtube and create a dictionary with song information
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet, contentDetails, statistics",
            myRating="like"
        )
        response = request.execute()

        # collect each video and get song and artist
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            # use youtube_dl to collect the song name and artist
            try:
                video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
                song_name = video["track"]
                #print('\n\n\n song_name', song_name)
                artist = video["artist"]
                #print("\n\n\n video ", video, '\n\n\n\n')
                # if liked video is a song, add the artist and song name to all_song_info
                spotify_uri = self.get_spotify_uri(song_name, artist)
                # song_info = {
                #     'song': song_name,
                #     'artist': artist,
                #     'uri': spotify_uri
                # }
                print("\n\n\n spotify_uri ", spotify_uri, '\n\n\n\n')
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name, 
                    "artist": artist,
                    "spotify_uri": spotify_uri
                }
            except:
                print(f'{youtube_url} is not a song')


    # create a playlist on Spotify
    def create_playlist(self):
        '''Function that crerates a spotiy playlist'''
        request_body = json.dumps({
            "name": "Lked YouTube videos",
             "description": "All liked videos on YoutTube",
             "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.spotify_id)

        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )

        response_json = response.json()
        print('token: ', self.spotify_token)
        print(response_json)

        # get the playlist id
        return response_json["id"]


    # Search for the song on spotify
    def get_spotify_uri(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name, 
            artist
        )

        print(query)

        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )

        response_json = response.json()

        print(response_json)
        songs=response_json["tracks"]["items"]
        uri = songs[0]["uri"]

        return uri


    # add song to Spotify playlist
    def add_songs_to_playlist(self):
        # populate songs dict
        self.get_liked_videos()

        # collect uri
        uris = []

        print('\n\n\n\n\n All song info: ', self.all_song_info)

        for song, info in self.all_song_info.items():
            uris.append(info["spotify_uri"])

        # create playlist
        playlist_id = self.create_playlist()

        # add songs to playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query, 
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )


if __name__ == "__main__":
    creator = CreatePlaylist()
    creator.add_songs_to_playlist()
    #print('WooHoo N Stuff')

    #test_url = creator.get_spotify_uri('Badfish', 'Sublime')

    #print(test_url)

    # youtube_url = "https://www.youtube.com/watch?v=9GCjRXUICac"

    # video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)

    # print(video.keys())