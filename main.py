#import os
import time
import spotipy as sp
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials

# IF YOU DON'T WANT TO HAVE YOUR CLIENT_ID AND CLIENT_SECRET EXPOSED YOU CAN HIDE IT WITHIN YOUR ENV VARIABLES:

# ON WINDOWS: 
# $env:SPOTIPY_CLIENT_ID=""
# $env:SPOTIPY_CLIENT_SECRET=""
# $env:SPOTIPY_REDIRECT_URI="" (ONLY IF USING AN ACCESS TOKEN TO ACCESS USER PROTECTED AREAS)

# ON LINUX:
# export SPOTIPY_CLIENT_ID=""
# export SPOTIPY_CLIENT_SECRET=""
# export SPOTIPY_REDIRECT_URI="" (ONLY IF USING AN ACCESS TOKEN TO ACCESS USER PROTECTED AREAS)

print('Working...')

start = time.time()
cpu_start = time.process_time()

client_id="0dc01299ed7c4203a5fd07e1a22c2df8"
client_secret="598854c46a5d4522b188a1afe884cc79"
spotify = sp.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id, client_secret))
#redirect_uri = "https://localhost:8888/callback"

artist = []
track = []
track_pop = []
duration_ms = []
album_nm = []
album_dt = []

#-------------------------------------------------------------------------------------------------------#
#                                                                                                       #
# RETURNS "POPULAR" SONGS FROM 2022-2023 | "POPULARITY" COMES FROM THE FORMULA USED BY SPOTIFY API      #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

def SearchPopularity():
  for index in range(0,500): # In the range() parameter you may increase or decrease the data collected
    query = sp.Spotify.search(self=spotify, q='year:2022-2023', type='track', limit=50, offset = index)
    for index, t in enumerate(query['tracks']['items']):
      artist.append(t['artists'][0]['name'])
      track.append(t['name'])
      track_pop.append(t['popularity'])
      duration_ms.append(t['duration_ms'])
      album_nm.append(t['album']['name'])
      album_dt.append(t['album']['release_date'])

  df = pd.DataFrame({'artist' : artist, 'track':track, 'track_pop':track_pop, 'duration_ms':duration_ms, 'album_nm':album_nm, 'album_dt':album_dt})
  df_clean = df.drop_duplicates('track')
  df_cleaned = df_clean.sort_values('track_pop', ascending=False)
  df_cleaned.to_csv('SpotifyDataframe.csv', sep=',', index=True, encoding = 'utf-8')

#-----------------------------------------------------------------------------------------------------------------#
#                                                                                                                 #
# RETURNS THE TOP PLAYED SONGS FROM 2023, THIS IS BASED ON THE "mostplayed_uri" PLAYLIST **UPDATED WEEKLY**       #
#                                                                                                                 #
#-----------------------------------------------------------------------------------------------------------------#

def topPlayed():
  mostplayed_url = 'https://open.spotify.com/playlist/2YRe7HRKNRvXdJBp9nXFza?si=67d0ac3567b04f42'
  for index in range(0,500): # In the range() parameter you may increase or decrease the data collected
    topQuery = spotify.playlist_items(playlist_id = mostplayed_url, offset=index, limit=50)
    for index, t in enumerate(topQuery['items']):
      artist.append(t['track']['artists'][0]['name'])
      track.append(t['track']['name'])
      track_pop.append(t['track']['popularity'])
      duration_ms.append(t['track']['duration_ms'])
      album_nm.append(t['track']['album']['name'])
      album_dt.append(t['track']['album']['release_date'])
  
  data = pd.DataFrame({'artist':artist, 'track':track, 'track_pop':track_pop, 'duration_ms':duration_ms, 'album_name':album_nm})
  #clean_Data = data.drop_duplicates('track')
  #sorted_data = clean_Data.sort_values('track_pop', ascending=False) # REVER, TALVEZ O IDEAL SEJA NAO ORDENARMOS
  data.to_csv('SpotifyTopPlayedQuery.csv', sep=',', index=True, encoding= "utf-8")

#------------------------------------------------------------------------------------------------------------------#
#                                                                                                                  #
# RETURNS THE TOP PLAYED SONGS FROM 2023, THIS IS BASED ON THE "mostplayedever_url" PLAYLIST **UPDATED WEEKLY**    #
#                                                                                                                  #
#------------------------------------------------------------------------------------------------------------------#



def Run():
  topPlayed()
  SearchPopularity()

Run()

#------------------------------------------------------------------------------------------------------------------#
#                                                                                                                  #
# USED TO TEST THE SCRIPT TIMELAPSE                                                                                #
#                                                                                                                  #
#------------------------------------------------------------------------------------------------------------------#

end = time.time()
cpu_end = time.process_time()

exec_ms = (end - start)/60
cpu_ms = cpu_end - cpu_start

print("The process finished sucessfully!")
time.sleep(0.5)
print("The csv files are available in the current folder.")
print('\n')
time.sleep(0.5)
print('Script exec time:', exec_ms)
print('CPU exec time:', cpu_ms)