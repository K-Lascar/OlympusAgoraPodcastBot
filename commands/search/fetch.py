from requests import get
from datetime import datetime
from sqlalchemy import MetaData, Table, Column, String, Integer
from re import sub
from pandas import DataFrame
from .fetch_helper import process_seconds, process_time_in_string, \
    modify_unicode_podcast_name, get_engine, check_episode_exist
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def create_database():
    engine = get_engine()
    metadata= MetaData(engine)
    create_table_podcast(metadata)
    metadata.create_all()

def create_table_podcast(metadata):
    Table("podcast", metadata,
    Column("Episode_Number", Integer, primary_key=True),
    Column("Title", String),
    Column("Description", String),
    Column("Duration", String),
    Column("Spotify_URL", String),
    Column("RSS_URL", String),
    Column("Publish_Timestamp", Integer))

# def create_table_fohmo3(metadata):
#     Table("fohmo", metadata,
#     Column("FOhmo_Day", Integer, primary_key=True),
#     Column("Title", String),
#     Column("Description", String),
#     Column("Duration", String),
#     Column("Spotify_URL", String),
#     Column("RSS_URL", String),
#     Column("Publish_Timestamp", Integer))


def update_podcast_table():
    engine = get_engine()

    credentials = SpotifyClientCredentials(client_secret = "663d871685104bd893ad67359aaae8c7", client_id = "327f342313dd4fcc85de17288bd910de")
    spotify = spotipy.Spotify(client_credentials_manager = credentials)

    # https://open.spotify.com/show/20aaSDPt7AF1fxShco8kyV?dl_branch=1
    spotify_results = spotify.show_episodes(show_id = "20aaSDPt7AF1fxShco8kyV",
        market = "ES")["items"]
    spotify_results = list(map(modify_unicode_podcast_name, spotify_results))
    i = 1
    while True:
        url = "https://apollo.rss.com/podcasts/agorapod/episodes?limit=5&page=" + str(i)
        i += 1
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cookie": "cookieClosed=true",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5"
        }

        resp_json = get(url = url, headers=headers).json()
        episodes = resp_json["episodes"]
        if episodes == []:
            break
        start_slice_index = 3
        for episode in episodes:
            podcast_dict = {}
            podcast_dict["Title"] = episode["title"]
            spotify_episode = list(filter(lambda s: s["name"] == podcast_dict["Title"], spotify_results))
            if spotify_episode == []:
                continue

            podcast_dict["Title"] = podcast_dict["Title"].strip()

            spotify_episode = spotify_episode[0]
            podcast_dict["Spotify_URL"] = spotify_episode["external_urls"]["spotify"]
            description = episode["description"]
            description = description[start_slice_index:description.index("</p>")]
            podcast_dict["Description"] = sub(r'[^\x00-\x7F]+',' ', description)
            publish_date = datetime.fromisoformat(episode["pub_date"][:-1]).timestamp()
            podcast_dict["Publish_Timestamp"] = int(publish_date)
            duration = int(spotify_episode["duration_ms"]) // 1000
            duration = process_seconds(duration)
            podcast_dict["Duration"] = process_time_in_string(*duration)
            # print(podcast_dict["Title"])
            # podcast_dict["Title"].startswith(("Ep", " Ep")) or
            if "itunes_episode" in episode.keys() and "itunes_season" in episode.keys():
                podcast_dict["Episode_Number"] = episode["itunes_episode"]
                podcast_dict["Season_Number"] = episode["itunes_season"]
            else:
                podcast_dict["Episode_Number"] = episode['id']
                podcast_dict["Season_Number"] = episode["itunes_season"]
                # podcast_dict["Season_Number"] = episode["itunes_season"]
            podcast_dict["RSS_URL"] = f"https://rss.com/podcasts/agorapod/{episode['id']}"
            if episode['episode_cover']:
                podcast_dict["Image_URL"] = f"https://media.rss.com/agorapod/{episode['episode_cover']}"
            else:
                podcast_dict["Image_URL"] = "https://media.rss.com/agorapod/20211127_091155_cc05c5183700ade08b3c46c2bc88f7a5.jpg"
            # update_season(episode['itunes_season'], podcast_dict["RSS_URL"])
            # # print(podcast_dict["Episode_Number"])
            if not check_episode_exist(podcast_dict["Episode_Number"], podcast_dict["RSS_URL"], podcast_dict["Season_Number"]):
                df = DataFrame(podcast_dict, index = [0])
                df.to_sql("podcast", engine, if_exists="append", index=False)


def update_season(season_num, rss_url):
    engine = get_engine()
    engine.execute("""
        UPDATE podcast
        SET Season_Number = ?
        WHERE RSS_URL = ?
    """, (season_num, rss_url))