import discord

import dbutils

import random
import re


def key():
    return random.choice(dbutils.get("settings", "keys"))


def get_prefix(bot, message):
    return dbutils.get("settings", "prefix")


async def log(ctx, title, description):
    title = f'LOG: {title}'
    if dbutils.read("settings")["logchannel"] != "":
        await discord.utils.get(ctx.guild.channels, name=dbutils.read("settings")["logchannel"]) \
            .send(embed=discord.Embed(title=title, description=description))


def remove_html(text):
    cleaner = re.compile("<.*?>")
    return re.sub(cleaner, '', text)
