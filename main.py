from config import discordBotKey
from discord.ext.commands import Bot
from discord_slash import SlashCommand, utils
from discord_components import DiscordComponents
from commands.search.search import get_all_episodes
from commands.search.fetch import update_podcast_table
from apscheduler.schedulers.background import BackgroundScheduler

# pip install -U git+https://github.com/Pycord-Development/pycord


class MyBot(Bot):
    def __init__(self):
        from discord import Intents
        intents = Intents.default()
        intents.members = True
        super().__init__(
            command_prefix="unused",
            self_bot=True,
            help_command=None,
            intents = intents
        )
        self.slash = SlashCommand(self, sync_commands=True,
            delete_from_unused_guilds=True)
        self.episodes = get_all_episodes()
        self.titles = list(map(lambda x: {"Title": x["Title"]}, self.episodes))
        self.descriptions = list(map(lambda x: {"Description": x["Description"]}, self.episodes))
        job_defaults = {
            "coalesce": False,
            "max_instances": 8
        }

        self.scheduler = BackgroundScheduler(
            job_defaults = job_defaults
        )

    async def resync_episodes(self):
        self.scheduler.add_job(update_podcast_table, "interval", seconds = 43200,
        start_date = self.get_time_delay(1))
        self.scheduler.start()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        DiscordComponents(self)
        await self.resync_episodes()
        # await utils.manage_commands.remove_all_commands(bot_id=896752038791237692, bot_token=discordBotKey)


    def get_time_delay(self, time):
        from datetime import datetime, timedelta
        current_time = datetime.now()
        time_delay = current_time + timedelta(seconds = time)
        return time_delay

bot = MyBot()

def check_member_has_role(member_roles, role_name):
    for member_role in member_roles:
        if role_name == member_role.name:
            return True
    return False

def load_cogs(bot: Bot):
    from pathlib import Path
    from pkgutil import iter_modules
    from os import listdir
    package_dir = Path(__file__).resolve().parent
    package_dir = Path.joinpath(package_dir, "commands", "cogs")
    files = listdir(package_dir)
    for info in files:
        if info in ["__pycache__"]:
            continue

        bot.load_extension(f"commands.cogs.{info[:-3]}")
    return bot


# To learn how to add descriptions, choices to options check slash_options.py
if __name__ == "__main__":
    load_cogs(bot)
    bot.run(discordBotKey)
