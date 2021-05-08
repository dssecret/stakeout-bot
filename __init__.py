import discord
from discord.ext import commands

import sys
import logging

import dbutils
import utils
from admin import Admin
from users import Users
from factions import Factions

assert sys.version_info >= (3, 6), "Requires Python 3.6 or newer"

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
discord_logger.addHandler(handler)

logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

dbutils.initialize()

bot = commands.Bot(command_prefix=utils.get_prefix, help_command=None)


@bot.event
async def on_ready():
    guild_count = 0

    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count += 1

    print(f'Bot is in {guild_count} guilds.')

    bot.add_cog(Admin(logger, bot))
    bot.add_cog(Users(logger, bot))
    bot.add_cog(Factions(logger, bot))


@bot.command()
async def ping(ctx):
    '''
    Returns the roundtrip ping to the server
    '''

    latency = bot.latency
    logger.info(f'Latency: {latency}')

    embed = discord.Embed()
    embed.title = "Latency"
    embed.description = f'{latency} seconds'
    await ctx.send(embed=embed)


@bot.command(brief="Returns prefix")
async def prefix(ctx):
    '''
    Returns the prefix for the bot
    '''

    embed = discord.Embed()
    embed.title = "Bot Prefix"
    embed.description = f'The bot prefix is {dbutils.read("settings")["prefix"]}.'
    await ctx.send(embed=embed)


@bot.command(brief="Return help message")
async def help(ctx, arg=None):
    '''
    Returns list of commands if no parameter is passed. If a command is passed as a parameter, the help command returns
    the help message of the passed command.
    '''

    embed = discord.Embed()
    p = dbutils.read("settings")["prefix"]

    if not arg:
        embed.title = "Help"
        embed.description = f'''
Total Commands: {len(bot.commands)}
Prefix: {p}

{p}ping: Pings the server hosting the bot and returns the ping
{p}prefix: Returns the bot's current prefix
{p}help: Returns the help message
{p}config: Sets or returns the configuration
{p}mkkey: Adds a Torn API key to the configuration
{p}rmkey: Removes a Torn API key from the configuration

*User Stakeouts*
{p}inituser: Initializes a user for a stakeout
{p}rmuser: Removes the stakeout on a user
{p}edituser: Adds or removes a stakeout key from/to a user
{p}lsusers: Returns a list of all staked-out users and watched keys

*Faction Stakeouts*

*Company Stakeouts*

*NOTE:* Not all commands can be run by everyone. Certain commands require the user to have the administrator permission.
        '''
    elif arg == "ping":
        embed.title = "Help: ping"
        embed.description = f"""
        **General Information**
        Returns the time between the bot's latency (more specifically, the latency between a HEARTBEAT and HEARBEAT_ACK).
        
        **Example**
        `{p}ping`
        """
    elif arg == "prefix":
        embed.title = "Help: prefix"
        embed.description = f"""
        **General Information**
        Returns the bot's current prefix as stored in the bot's JSON settings file. This may not accurately reflect the prefix of the bot while the bot's being run as the bot needs to be restarted for the changed prefix to take effect. Mentioning the bot is always an alternative to using the bot's prefix.
        
        **Example**
        `{p}prefix`
        """
    elif arg == "help":
        embed.title = "Help: help [command]"
        embed.description = f"""
        **General Information**
        Returns a help message with a basic overview if no command is passed as an argument. If a command is passed as an argument, a specific help message with the general information, argument(s) (if required), and examples will be returned.
        
        **Argument**
        command (optional) - the command whose help message is to be returned (possible arguments include `buy`, `log`, and `config`)
        
        **Examples**
        `{p}help`
        `{p}help blacklist`
        """
    elif arg == "config":
        embed.title = "Help: config [key] [value]"
        embed.description = f"""
        **Genral Information**
        Returns the bot's configuration if no argument is passed. If argument(s) are passed, the bot sets the value of the first argument passed with the second argument (the first argument is the key and the second argument is the value).
        This command requires the command invoker to have the Administrator permission in the server from which the command is invoked.
        
        **Arguments**  
        For all current, possible arguments, a value must be passed.
        ac - the key for the stakeout category (the category where all stakeout channels will be created)
        prefix - the key for the prefix; a string must be passed as the value
        
        **Examples**
        `{p}config`
        `{p}config sc stakeouts`
        `{p}config prefix !`
        """
    elif arg == "mkkey":
        embed.title = "Help: mkkey [key]"
        embed.description = f"""
        **General Information**
        Adds the specified Torn API key to the bot's configuration. The bot will first check whether the API key is authentic. The API key can be permanently removed from the configuration with the `rmkey` command.
        NOTE: The bot does automatically delete the invocation message to prevent a malicious user from copying the key.
        
        **Arguments**
        key - the Torn API key
        
        **Examples**
        `{p}mkkey ABC123DEF456`
        """
    elif arg == "rmkey":
        embed.title = "Help: rmkey [key]"
        embed.description = f"""
        **General Information**
        Removes the specified API key from the bot's configuration.
        NOTE: The bot does automatically delete the invocation message to prevent a malicious user from copying the key.
        
        **Arguements**
        key - the Torn API key
        
        **Examples**
        `{p}mkkey ABC123DEF456`
        """
    elif arg == "inituser":
        embed.title = "Help: inituser [id]"
        embed.description = f"""
        **General Information**
        Initializes a stakeout of the specified user.
        
        **Arguments**
        id - the user's Torn ID
        
        **Examples*
        `{p}inituser 2383326`
        """
    elif arg == "rmuser":
        embed.title = "Help: rmuser [id]"
        embed.description = f"""
        **General Information**
        Removes the stakeout of the specified user if one exists.
        
        **Arguments**
        id - the user's Torn ID
        
        **Examples*
        `{p}rmuser 2383326`
        """
    elif arg == "edituser":
        embed.title = "Help: edituser [id] [key]"
        embed.description = f"""
        **General Information**
        Adds or removes the specified stakeout key from the specified user. 
        
        **Arguments**
        id - the user's Torn ID
        key - Values to be watched in the staked-out user
        
        **Keys**
        level - watches for changes in the user's level
        okay - watches to see when a user has left hospital
        landed - watches to see when a user has landed in a foreign country
        online - watches to see when a user has come online from being idle (at least five minutes from last action) or offline
        offline - watches to see when a user has come offline from being idle (at least five minutes from last action) or online
        
        **Examples**
        `{p}edit user 2383326 level`
        `{p}edit user 2383326 okay`
        `{p}edit user 2383326 landed`
        `{p}edit user 2383326 online`
        `{p}edit user 2383326 offline`
        """
    elif arg == "lsusers":
        embed.title = "Help: lsusers"
        embed.description = f"""
        **General Information**
        Returns a list of staked-out users and their respective keys
        
        **Examples**
        `{p}lsusers`
        """
    elif arg == "initcompany":
        embed.title = "Help: initcompany [id]"
        embed.description = f"""
        **General Information**
        Initializes a stakeout of the specified company.
        
        **Arguments**
        id - the company's Torn ID
        
        **Examples*
        `{p}initcompany 86932`
        """
    elif arg == "rmcompany":
        embed.title = "Help: rmcompany [id]"
        embed.description = f"""
        **General Information**
        Removes the stakeout of the specified company if one exists.
        
        **Arguments**
        id - the company's Torn ID
        
        **Examples*
        `{p}rmcompany 86932`
        """
    elif arg == "editcompany":
        embed.title = "Help: editcompany [id] [key]"
        embed.description = f"""
        **General Information**
        Adds or removes the specified stakeout key from the specified company. 
        
        **Arguments**
        id - the company's Torn ID
        key - Values to be watched in the staked-out company
        
        **Keys**
        members - watches to see when a member leaves or joins the company
        
        **Examples**
        `{p}edit company 86932 members`
        """
    elif arg == "lscompaniess":
        embed.title = "Help: lscompanies"
        embed.description = f"""
        **General Information**
        Returns a list of staked-out companies and their respective keys
        
        **Examples**
        `{p}lscompanies`
        """
    elif arg == "initfaction":
        embed.title = "Help: initfaction [id]"
        embed.description = f"""
        **General Information**
        Initializes a stakeout of the specified faction.
        
        **Arguments**
        id - the faction's Torn ID
        
        **Examples*
        `{p}initfaction 22680`
        """
    elif arg == "rmfaction":
        embed.title = "Help: rmfaction [id]"
        embed.description = f"""
        **General Information**
        Removes the stakeout of the specified faction if one exists.
        
        **Arguments**
        id - the faction's Torn ID
        
        **Examples*
        `{p}rmfaction 22680`
        """
    elif arg == "editfaction":
        embed.title = "Help: editfaction [id] [key]"
        embed.description = f"""
        **General Information**
        Adds or removes the specified stakeout key from the specified faction. 
        
        **Arguments**
        id - the faction's Torn ID
        key - Values to be watched in the staked-out faction
        
        **Keys**
        territory - watches for changes in the faction's territories (and rackets if applicable)
        members - watches for changes in the faction's members list
        memberstatus - watches for changes in the faction's members' status (okay, in hosp, flying, etc.)
        memberactivity - watches for changes in the faction's members' activity (online or offline)
        
        **Examples**
        `{p}edit faction 22680 territory`
        `{p}edit faction 22680 members`
        `{p}edit faction 22680 memberstatus`
        `{p}edit faction 22680 memberactivity`
        """
    elif arg == "lsfactions":
        embed.title = "Help: lsfactions"
        embed.description = f"""
        **General Information**
        Returns a list of staked-out factions and their respective keys
        
        **Examples**
        `{p}lsfactions`
        """
    else:
        embed.description = "This command does not exist."

    await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.run(dbutils.get("settings", "bottoken"))
