from discord import Embed
from sqlalchemy.sql.expression import desc
from .fetch_helper import get_engine
from thefuzz import process

def create_fuzzed_embed(author_name, author_img, num_of_episodes, query, query_type):
    image_url = "https://cdn.discordapp.com/attachments/901093983869087745/903797340232626236/unknown.png"

    title = f'Could not find episode Episode {query_type} for "{query}"!'
    description = f"Found **{num_of_episodes} possible matches.**\n"
    description += "Please select an episode from the dropdown menu.\n"
    embed = Embed(title = title, description = description, colour = 0xFFFFFF)
    embed.set_author(name = author_name, icon_url=author_img)
    embed.set_thumbnail(url = image_url)

    embed.set_footer(text = "\u200B", icon_url=image_url)

    return embed

# ALTER TABLE podcast
# ADD Image_URL VARCHAR
# CONSTRAINT default_constraint DEFAULT "https://cdn.discordapp.com/attachments/901093983869087745/903797340232626236/unknown.png"

def create_podcast_info_embed(author_name, author_img, episode_dict):
    image_url = episode_dict["Image_URL"]
    published_date = episode_dict["Publish_Timestamp"]
    duration = episode_dict["Duration"]
    description = episode_dict["Description"]
    episode_title = episode_dict["Title"]

    title = episode_title
    description = f"**Description:** {description}\n\n"
    description += f"**Published Date:** <t:{published_date}:R>\n"
    description += f"**Duration:** {duration}\n"

    embed = Embed(title = title, description = description, colour = 0xFFFFFF)
    embed.set_author(name = author_name, icon_url=author_img)
    embed.set_thumbnail(url = image_url)
    embed.set_footer(text = "\u200B", icon_url=image_url)

    return embed


def find_episode(episode_number, season_number):
    engine = get_engine()
    result = engine.execute("""
        SELECT *
        FROM podcast
        WHERE Episode_Number = ? and Season_Number = ?
    """, (episode_number, season_number)).fetchone()
    return result

def get_all_episodes():
    engine = get_engine()
    result = engine.execute("""
        SELECT *
        FROM podcast
    """).fetchall()
    result = [{column: value for column, value in proxy.items()} for proxy in result]
    return result

def get_recent_episode():
    engine = get_engine()
    result = engine.execute("""
        SELECT *
        FROM podcast
        ORDER BY Publish_Timestamp DESC
        LIMIT 1
    """).fetchone()
    # result = [{column: value for column, value in proxy.items()} for proxy in result]
    result = {column: value for column, value in result.items()}
    return result

def search_by_episode_number(episode_num, season_num = 1):
    if episode_num:
        result = find_episode(episode_num, season_num)
        if result:
            result = {column: value for column, value in result.items()}
            return result

    return None

def find_question_in_list(query, query_type, episode_list):
    return list(filter(lambda x: x[query_type] == query[query_type], episode_list))[0]


def search_by_query_list(term, query_list):
    result = process.extract(term, query_list, limit = 5)
    # query_result = [find_question_in_list(result[i][0], query_type, episode_list) for i in range(5)]
    return result
