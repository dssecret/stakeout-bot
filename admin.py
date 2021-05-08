import discord
from discord.ext import commands
import requests

import dbutils
import utils

import datetime


class Admin(commands.Cog):
    def __init__(self, logger, bot):
        self.logger = logger
        self.bot = bot

    @staticmethod
    def check_admin(member: discord.Member):
        return True if member.guild_permissions.administrator else False

    @commands.command()
    async def config(self, ctx, arg=None, value=None):
        '''
        Returns the current configuration of the bot
        '''

        if not self.check_admin(ctx.message.author):
            embed = discord.Embed()
            embed.title = "Permission Denied"
            embed.description = f'This command requires {ctx.message.author.name} to be an Administrator. ' \
                                f'This interaction has been logged.'
            await ctx.send(embed=embed)

            self.logger.warning(f'{ctx.message.author.name} has attempted to run config, but is not an Administrator')
            return None

        embed = discord.Embed()

        if not arg:
            embed.title = "Configuration"
            embed.description = f'''Bot Token: Classified
            Prefix: {dbutils.get("settings", "prefix")}
            Stakeout Category: {dbutils.get("settings", "stakeout")}
            '''
        # Configurations that require a value below here
        elif not value:
            embed.title = "Value Error"
            embed.description = "A value must be passed"
        elif arg == "log":
            for channel in ctx.guild.channels:
                if str(channel.id) != value[2:-1]:
                    continue
                data = dbutils.read("settings")
                data["logchannel"] = channel.name
                dbutils.write("settings", data)
                self.logger.info(f'Log Channel has been set to {data["logchannel"]}.')
                embed.title = "Log Channel"
                embed.description = f'Ad Channel has been set to {data["logchannel"]}.'
                await utils.log(ctx, "Log Channel", f'The log channel has been set to {value} by '
                                                    f'{ctx.message.author.name}.')
        elif arg == "prefix":
            data = dbutils.read("guilds")

            for guild in data["guilds"]:
                if guild["id"] == str(ctx.guild.id):
                    guild["prefix"] = str(value)

            dbutils.write("guilds", data)
            self.logger.info(f'Bot Prefix has been set to {value}.')
            embed.title = "Bot Prefix"
            embed.description = f'Bot Prefix has been set to {value}.'
            await utils.log(ctx, "Prefix", f'The prefix has been set to {value} by {ctx.message.author.name}.')
        elif arg == "sc":
            for category in ctx.guild.categories:
                if str(category.name) != value:
                    continue
                data = dbutils.read("settings")
                data["stakeout"] = category.name
                dbutils.write("settings", data)
                self.logger.info(f'Stakeout category has been set to {data["stakeout"]} by {ctx.message.author.name}.')
                embed.title = "Stakeout Category"
                embed.description = f'Stakeout category has been set to {data["stakeout"]}.'
                await utils.log(ctx, "Stakeout Category", f'The stakeout category has been set to {data["stakeout"]} '
                                                          f'by {ctx.message.author.name}.')
                continue
        else:
            embed.title = "Configuration"
            embed.description = "This key is not a valid configuration key."

        await ctx.send(embed=embed)

    @commands.command()
    async def mkkey(self, ctx, key):
        '''
        Adds a Torn API Key to the config after checking the key
        '''

        await ctx.message.delete()
        request = requests.get(f'https://api.torn.com/user/?selections=&key={key}&comment=SB')

        if request.status_code != 200:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Something has possibly gone wrong with the request to the Torn API with ' \
                                f'HTTP status code {request.status_code} has been given at ' \
                                f'{datetime.datetime.now()}.'
            await ctx.send(embed=embed)
            self.logger.error(f'The Torn API has responded with HTTP status code {request.status_code}.')
            return Exception

        if 'error' in request.json():
            error = request.json()['error']
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Something has gone wrong with the request to the Torn API with error code ' \
                                f'{error["code"]} ({error["error"]}). Visit the [Torn API documentation]' \
                                f'(https://api.torn.com/) to see why the error was raised.'
            await ctx.send(embed=embed)
            self.logger.error(f'The Torn API has responded with error code {error["code"]}.')
            raise Exception

        data = dbutils.read("settings")
        data["keys"].append(key)
        data["keys"] = list(set(data["keys"]))
        dbutils.write("settings", data)
        self.logger.info(f'{ctx.message.author.name} has added {request.json()["name"]}\'s {key} to the bot.')

        embed = discord.Embed()
        embed.title = "Key Added"
        embed.description = f'{request.json()["name"]}\'s key has been added to the bot\'s list of keys by ' \
                            f'{ctx.message.author.name}.'
        await ctx.send(embed=embed)

        await utils.log(ctx, "Key Added", f'{request.json()["name"]}\'s key has been added to the bot\'s list of keys '
                                          f'by {ctx.message.author.name}.')

    @commands.command()
    async def rmkey(self, ctx, key):
        '''
        Removes a Torn API Key to the config after checking the key
        '''

        await ctx.message.delete()

        data = dbutils.read("settings")
        data["keys"].remove(key)
        dbutils.write("settings", data)
        self.logger.info(f'{ctx.message.author.name} has {key} from the bot.')

        embed = discord.Embed()
        embed.title = "Key Removed"
        embed.description = f'A key has been removed from the bot\'s list of keys by {ctx.message.author.name}.'
        await ctx.send(embed=embed)
