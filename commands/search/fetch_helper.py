from unicodedata import normalize
from sqlalchemy import create_engine
def process_seconds(total_seconds):
    hours, remainder = divmod(total_seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    return (hours, minutes)

def process_time_in_string(hours, minutes):
    time_string = ""
    if hours > 0:
        time_string += f"{hours} "
        time_string += "hours" if hours > 1 else "hour"
        if minutes > 0:
            time_string += ", "
    if minutes > 0:
        time_string += f"{minutes} "
        time_string += "minutes" if minutes > 1 else "minute"
    time_string += "."
    return time_string

def modify_unicode_podcast_name(podcast_dict):
    podcast_dict["name"] = normalize("NFKD", podcast_dict["name"])
    return podcast_dict

def get_engine():
    engine = create_engine("sqlite:///agora.db")
    return engine

def check_episode_exist(episode_number, rss_link, season_number):
    engine = get_engine()
    return engine.execute(
        """
            SELECT Episode_Number
            FROM podcast
            WHERE (Episode_Number = ? and Season_Number = ?) or RSS_URL = ?
        """, (episode_number, season_number, rss_link)).fetchone() != None
