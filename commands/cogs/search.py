from discord.ext import commands
from asyncio import sleep, TimeoutError
from discord_slash import SlashContext, cog_ext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_actionrow, \
    create_button, create_select, create_select_option, wait_for_component
from commands.search.search import search_by_query_list, \
    search_by_episode_number, get_recent_episode, create_fuzzed_embed, \
    create_podcast_info_embed
from commands.search.search_helper import format_episode_title
from discord_slash.utils.manage_commands import create_option, create_choice
class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def find_question_in_list(self, query, query_type):
        return list(filter(lambda x: x[query_type] == query[query_type], self.bot.episodes))[0]

    def process_fuzzed_info(self, fuzzed_results):
        options = []
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        counter = 0
        for result in fuzzed_results:
            episode_dict, percent_match = result
            query_type = "Title" if "Title" in episode_dict.keys() else "Description"
            episode_dict = self.find_question_in_list(episode_dict, query_type)
            label = format_episode_title(episode_dict["Title"])

            if any(x['label'] == label for x in options):
                continue
            if counter == 0:
                description = "Best Match: "
            else:
                description = "Other Match: "

            options.append(
                create_select_option(
                    label = label,
                    description = f"{description} {percent_match} % match",
                    value=f"{episode_dict['Episode_Number']}:{episode_dict['Season_Number']}",
                    emoji = emojis[counter]
                )
            )
            counter += 1

        select_options = create_select(
            placeholder= "Select a episode from the list!",
            options = options
        )

        select_options = [create_actionrow(select_options)]
        return select_options

    def process_podcast_info(self, podcast_dict):

        spotify_button = create_button(
            style = ButtonStyle.URL,
            emoji = {"id": 909436330063302727, "emoji" : "spotify"},
            label="Spotify",
            url = podcast_dict["Spotify_URL"]
        )
        rss_button = create_button(
            style = ButtonStyle.URL,
            emoji = {"id": 909437938188840990, "emoji" : "rss"},
            label="RSS",
            url = podcast_dict["RSS_URL"]
        )
        google_button = create_button(
            style = ButtonStyle.URL,
            emoji = {"id": 909436058440192020, "emoji" : "google_podcast"},
            label="Google Podcasts",
            url = "https://podcasts.google.com/feed/aHR0cHM6Ly9tZWRpYS5yc3MuY29tL2Fnb3JhcG9kL2ZlZWQueG1s"
        )
        apple_button = create_button(
            style = ButtonStyle.URL,
            emoji = {"id": 909435922108534796, "emoji" : "apple_podcast"},
            label="Apple Podcasts",
            url = "https://podcasts.apple.com/us/podcast/agora-podcast-olympus-community-podcast/"
        )
        # mp3_button = create_button(
        #     style = ButtonStyle.URL,
        #     emoji = "🎧",
        #     label="MP3 File",
        #     url = "https://podcasts.apple.com/us/podcast/agora-podcast-olympus-community-podcast/"
        # )


        buttons = [spotify_button, rss_button, google_button, apple_button]
        buttons_options = [create_actionrow(*buttons)]
        return buttons_options


    @cog_ext.cog_subcommand(
        base = "search",
        name = "episode",
        description = "Finds episode on the Agora Podcast by the episode number.",
        options = [
            create_option(
                name = "number",
                description = "Episode number from the Agora Podcast!",
                option_type = 4,
                required = False,
            ),
            create_option(
                name = "season",
                description = "Season number from the Agora Podcast!",
                option_type = 4,
                required = False,
            ),
        ],
        guild_ids = [
            751595790559871056,
            798328113087119371
        ]
    )
    async def search_by_episode_num(self, ctx, number = None, season = None):
        await ctx.defer()

        if number:
            if season:
                results = search_by_episode_number(number, season)
            else:
                results = search_by_episode_number(number)
            fuzzed_results = results

            if fuzzed_results:
                print(fuzzed_results)
                await ctx.send(fuzzed_results["Spotify_URL"])
            else:
                if season:
                    await ctx.send(f"Sorry, I could not find episode number {number} for season {season}")
                else:
                    await ctx.send(f"Sorry, I could not find episode number {number} for season 1")
        else:
            episode = get_recent_episode()
            await ctx.send(episode["Spotify_URL"])

    @cog_ext.cog_subcommand(
        base = "search",
        name = "title",
        description = "You can query episodes on the Agora Podcast by their title.",
        options = [
            create_option(
                name = "query",
                description = "Query by episode title from the Agora Podcast!",
                option_type = 3,
                required = False,
            ),
        ],
        guild_ids = [
            751595790559871056,
            798328113087119371
        ]
    )
    async def search_by_episode_title(self, ctx, query = None):
        # await ctx.defer(hidden=True)
        query_type = "Title"
        if query:
            fuzzed_results = search_by_query_list(query, self.bot.titles)
            filtered_results = list(filter(lambda x: x[1] >= 85, fuzzed_results))
            filtered_results_length = len(filtered_results)

            if filtered_results_length > 1:
                fuzzed_results = filtered_results
            elif filtered_results_length == 1:
                filtered_results = self.find_question_in_list(filtered_results[0][0], "Title")
                await ctx.send(filtered_results["Spotify_URL"])
                return

            author_name = ctx.author.name
            author_img = ctx.author.avatar_url


            select_options = self.process_fuzzed_info(fuzzed_results)
            fuzzed_results_length = len(select_options[0]['components'][0]['options'])

            episode_embed = create_fuzzed_embed(author_name, author_img,
                fuzzed_results_length, query, query_type)
            await ctx.send(embed= episode_embed,
            components = select_options, hidden =True)
            msg_response = await wait_for_component(self.bot, components=select_options[0])
                # msg_response = await self.bot.wait_for("select_option",
                            # check = lambda inter: inter.author.id == author_id and
                                # inter.message.id == option_msg.id, timeout=120)
            preference = msg_response.values[0]
            episode_num, season_num = tuple(preference.split(":"))
            preference_result = search_by_episode_number(episode_num, season_num)
            # preference_result = list(filter(lambda x: str(x["Episode_Number"]) == preference, self.bot.episodes))[0]
            await msg_response.send(preference_result["Spotify_URL"])
            # select_options[0]["components"][0]["disabled"] = True
            # print(option_msg)
            # await option_msg.edit_origin(embed = episode_embed, components = select_options)

        else:
            episode = get_recent_episode()
            await ctx.send(episode["Spotify_URL"])

    @cog_ext.cog_subcommand(
        base = "search",
        name = "info",
        description = "You can query episodes on the Agora Podcast by their title/description/episode number.",
        options = [
            create_option(
                name = "query",
                description = "Query episode on the Agora Podcast!",
                option_type = 3,
                required = False,
            ),
        ],
        guild_ids = [
            751595790559871056,
            798328113087119371
        ]
    )
    async def search_by_episode_info(self, ctx, query = None):
        author_name = ctx.author.name
        author_img = ctx.author.avatar_url
        if query:
            # print(query)
            if query.isdecimal():
                number = int(query)
                fuzzed_result = search_by_episode_number(number)
                print(fuzzed_result)
                if fuzzed_result:
                    podcast_info_embed = create_podcast_info_embed(author_name, author_img, fuzzed_result)
                    print(fuzzed_result)
                    button_options = self.process_podcast_info(fuzzed_result)
                    await ctx.send(embed= podcast_info_embed,
                    components = button_options)
                else:
                    await ctx.send(f"Sorry, I could not find episode number {query}")
            fuzzed_title_results = search_by_query_list(query, self.bot.titles)
            fuzzed_description_results = search_by_query_list(query, self.bot.descriptions)
            fuzzed_results = fuzzed_title_results + fuzzed_description_results
            fuzzed_results = fuzzed_results[:5]
            fuzzed_results.sort(key = lambda x: x[1], reverse=True)

            filtered_results = list(filter(lambda x: x[1] >= 85, fuzzed_results))
            filtered_results_length = len(filtered_results)


            if filtered_results_length > 1:
                fuzzed_results = filtered_results
            elif filtered_results_length == 1:
                filtered_results = self.find_question_in_list(filtered_results[0][0], "Title")
                await ctx.send(filtered_results["Spotify_URL"])
                return


            select_options = self.process_fuzzed_info(fuzzed_results)
            fuzzed_results_length = len(select_options[0]['components'][0]['options'])
            episode_embed = create_fuzzed_embed(author_name, author_img,
                fuzzed_results_length, query, "Info")

            await ctx.send(embed= episode_embed,
            components = select_options, hidden=True)
            msg_response = await wait_for_component(self.bot, components=select_options[0])
            preference = msg_response.values[0]
            episode_num, season_num = tuple(preference.split(":"))
            # preference_result = list(filter(lambda x: str(x["Episode_Number"]) == preference, self.bot.episodes))[0]
            preference_result = search_by_episode_number(episode_num, season_num)
            podcast_info_embed = create_podcast_info_embed(author_name, author_img, preference_result)

            button_options = self.process_podcast_info(preference_result)
            await msg_response.send(embed= podcast_info_embed,
            components = button_options)

        else:
            episode = get_recent_episode()
            await ctx.send(episode["Spotify_URL"])

def setup(bot):
    bot.add_cog(Search(bot))
