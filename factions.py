import discord
from discord.ext import commands, tasks
import requests
from aiohttp import ClientSession

import dbutils
import utils

import datetime
import asyncio
import json
import time


class Factions(commands.Cog):
    def __init__(self, logger, bot):
        self.logger = logger
        self.bot = bot

        self.update_factions.start()

    @tasks.loop(minutes=1)
    async def update_factions(self):
        start = time.time()

        async def get(url, session):
            async with session.get(url) as response:
                return await response.read()

        data = dbutils.read("stakeouts")
        tasks = []
        async with ClientSession() as session:
            for faction in data["factions"]:
                task = asyncio.ensure_future(get(f'https://api.torn.com/faction/{faction}?selections=basic,'
                                                 f'territory&key={utils.key()}', session))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            responses = [json.loads(response.decode('UTF-8')) for response in responses]

            for faction in responses:
                keys = data["factions"][str(faction["ID"])]["keys"]
                channel = discord.utils.get(self.bot.guilds[0].channels, name=f'faction-{faction["tag"].lower()}')

                if "territory" in keys and data["factions"][str(faction["ID"])]["territory"] != faction["territory"]:
                    for territoryid, territory in data["factions"][str(faction["ID"])]["territory"].items():
                        if territoryid not in faction["territory"]:
                            embed = discord.Embed()
                            embed.title = "Territory Removed"
                            embed.description = f'The territory {territoryid} of staked out faction ' \
                                                f'{faction["name"]} has been removed from that faction.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                    for territoryid, territory in faction["territory"].items():
                        if territoryid not in data["factions"][str(faction["ID"])]["territory"]:
                            embed = discord.Embed()
                            embed.title = "Territory Added"
                            embed.description = f'The territory {territoryid} of staked out faction ' \
                                                f'{faction["name"]} has been added to that faction.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                    for territoryid, territory in faction["territory"].items():
                        if "racket" not in territory:
                            continue
                        elif territory["racket"] == \
                                data["factions"][str(faction["ID"])]["territory"][territoryid]["racket"]:
                            continue

                        if "racket" not in territory and "racket" in \
                                data["factions"][str(faction["ID"])]["territory"][territoryid]:
                            embed = discord.Embed()
                            embed.title = "Racket Gained"
                            embed.description = f'A racked at {territoryid} has been gained by faction. ' \
                                                f'The racket is {territory["racket"]["name"]} ' \
                                                f'and gives {territory["racket"]["reward"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                        if territory["racket"]["level"] > data["factions"][str(faction["ID"])]["territory"][territoryid]["racket"]["level"]:
                            embed = discord.Embed()
                            embed.title = "Racket Leveled Up"
                            embed.description = f'The racket at {territoryid} has levelled up. The racket is ' \
                                                f'{territory["racket"]["name"]} now gives ' \
                                                f'{territory["racket"]["reward"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)
                        elif territory["racket"]["level"] < data["factions"][str(faction["ID"])]["territory"][territoryid]["racket"]["level"]:
                            embed = discord.Embed()
                            embed.title = "Racket Downgraded"
                            embed.description = f'The racket at {territoryid} has downgraded. The racket is ' \
                                                f'{territory["racket"]["name"]} now gives ' \
                                                f'{territory["racket"]["reward"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                    for territoryid, territory in data["factions"][str(faction["ID"])]["territory"].items():
                        if "racket" not in territory:
                            continue

                        if "racket" in territory and "racket" not in faction["territory"][territoryid]:
                            embed = discord.Embed()
                            embed.title = "Racket Lost"
                            embed.description = f'A racked at {territoryid} has been lost by staked out faction. ' \
                                                f'The racket was ' \
                                                f'{data["factions"][str(faction["ID"])]["territory"][territoryid]["racket"]["name"]} ' \
                                                f'and gives ' \
                                                f'{data["factions"][str(faction["ID"])]["territory"][territoryid]["racket"]["reward"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                if "members" in keys and data["factions"][str(faction["ID"])]["members"] != faction["members"]:
                    for memberid, member in data["factions"][str(faction["ID"])]["members"].items():
                        if memberid not in faction["members"]:
                            embed = discord.Embed()
                            embed.title = "Member Left"
                            embed.description = f'Member {member["name"]} has left the staked out faction ' \
                                                f'{faction["name"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                    for memberid, member in faction["members"].items():
                        if memberid not in data["factions"][str(faction["ID"])]["members"]:
                            embed = discord.Embed()
                            embed.title = "Member Joined"
                            embed.description = f'Member {member["name"]} has joined the staked out faction ' \
                                                f'{faction["name"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                if "memberstatus" in keys and data["factions"][str(faction["ID"])]["members"] != faction["members"]:
                    for memberid, member in data["factions"][str(faction["ID"])]["members"].items():
                        if memberid not in faction["members"]:
                            continue

                        if member["status"]["description"] != faction["members"][memberid]["status"]["description"] \
                                or member["status"]["state"] != faction["members"][memberid]["status"]["state"]:
                            if member["status"]["details"] == faction["members"][memberid]["status"]["details"]:
                                continue

                            embed = discord.Embed()
                            embed.title = "Member Status Change"
                            embed.description = f'Member {member["name"]} of staked out faction {faction["name"]} ' \
                                                f'has had their status changed from ' \
                                                f'{member["status"]["description"]} to ' \
                                                f'{faction["members"][memberid]["status"]["description"]}' \
                                                f'{"" if member["status"]["details"] == "" else " because " + utils.remove_html(member["status"]["details"])}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                if "memberactivity" in keys and data["factions"][str(faction["ID"])]["members"] != faction["members"]:
                    for memberid, member in data["factions"][str(faction["ID"])]["members"].items():
                        if memberid not in faction["members"]:
                            continue

                        if member["last_action"]["status"] in ("Offline", "Idle") and \
                                faction["members"][memberid]["last_action"]["status"] == "Online":
                            if faction["members"][memberid]["last_action"]["status"] == "Idle" and \
                                    datetime.datetime.now(datetime.timezone.utc).timestamp() - \
                                    faction["members"][memberid]["last_action"]["timestamp"] < 300:
                                continue

                            embed = discord.Embed()
                            embed.title = "Status Change"
                            embed.description = f'The status of {member["name"]} in staked out faction ' \
                                                f'{faction["name"]} has changed from ' \
                                                f'{member["last_action"]["status"]} to ' \
                                                f'{faction["members"][memberid]["last_action"]["status"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)
                        elif member["last_action"]["status"] in ("Online", "Idle") and \
                                faction["members"][memberid]["last_action"]["status"] in ("Offline", "Idle"):
                            if faction["members"][memberid]["last_action"]["status"] == "Idle" and \
                                    datetime.datetime.now(datetime.timezone.utc).timestamp() - \
                                    faction["members"][memberid]["last_action"]["timestamp"] < 300:
                                continue
                            if faction["members"][memberid]["last_action"]["status"] == "Idle" \
                                    and member["last_action"]["status"] == "Idle":
                                continue

                            embed = discord.Embed()
                            embed.title = "Status Change"
                            embed.description = f'The status of {member["name"]} in staked out faction ' \
                                                f'{faction["name"]} has changed from ' \
                                                f'{member["last_action"]["status"]} to ' \
                                                f'{faction["members"][memberid]["last_action"]["status"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                data["factions"][str(faction["ID"])] = faction
                data["factions"][str(faction["ID"])]["keys"] = keys
            dbutils.write("stakeouts", data)

        self.logger.info(f'Auto-updater for factions run in {time.time() - start} seconds.')

    @commands.command()
    async def initfaction(self, ctx, id: int):
        data = dbutils.read("stakeouts")

        if id in data["factions"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Faction ID {id} is already being staked out.'
            await ctx.send(embed=embed)
            raise Exception

        request = requests.get(f'https://api.torn.com/faction/{id}?selections=basic,territory&key={utils.key()}')

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

        data["factions"][str(id)] = request.json()
        data["factions"][str(id)]["keys"] = []
        dbutils.write("stakeouts", data)

        await ctx.guild.create_text_channel(
            f'faction-{request.json()["tag"]}',
            category=discord.utils.get(ctx.guild.categories, name=dbutils.get("settings", "stakeout"))
        )

        embed = discord.Embed()
        embed.title = "Faction Stakeout Added"
        embed.description = f'The stakeout of faction ID {id}, {request.json()["name"]}, has been added.'
        await ctx.send(embed=embed)

        await utils.log(ctx, "Faction Stakeout Added", f'The stakeout of {id} has been added by '
                                                       f'{ctx.message.author.name}.')
        self.logger.info(f'The stakeout of faction {id} has been added by {ctx.message.author.name}.')

    @commands.command()
    async def rmfaction(self, ctx, id: int):
        data = dbutils.read("stakeouts")

        if str(id) not in data["factions"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Faction {id} is not currently being staked out.'
            await ctx.send(embed=embed)
            return Exception

        channel = discord.utils.get(ctx.guild.channels, name=f'faction-{data["factions"][str(id)]["tag"]}')
        await channel.delete()

        data["factions"].pop(str(id))
        dbutils.write("stakeouts", data)

        try:
            embed = discord.Embed()
            embed.title = "Faction Stakeout Removed"
            embed.description = f'The stakeout of faction ID {id} has been removed.'
            await ctx.send(embed=embed)
        except:
            pass

        await utils.log(ctx, "Faction Stakeout Removed", f'The stakeout of {id} has been removed by '
                                                         f'{ctx.message.author.name}.')
        self.logger.info(f'The stakeout of faction {id} has been removed by {ctx.message.author.name}.')

    @commands.command()
    async def editfaction(self, ctx, id: int, key: str):
        data = dbutils.read("stakeouts")
        valid_keys = ["territory", "members", "memberstatus", "memberactivity"]

        if str(id) not in data["factions"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Faction {id} is not currently being staked out.'
            await ctx.send(embed=embed)
            return Exception

        if key not in valid_keys:
            embed = discord.Embed()
            embed.title = "Invalid Key"
            embed.description = f'The given key, {key}, is not valid. Please make sure that you\'r using a valid key,'
            await ctx.send(embed=embed)
            return Exception

        embed = discord.Embed()
        embed.title = "Faction Stakeout Modified"

        if key in data["factions"][str(id)]["keys"]:
            data["factions"][str(id)]["keys"].pop(key)
            embed.description = f'{key} has been removed from the triggers of {data["factions"][str(id)]["name"]}.'
            await utils.log(ctx, "Faction Stakeout Modified", f'The stakeout of {id} has been modified by '
                                                              f'{ctx.message.author.name} to remove {key}.')
            self.logger.info(f'The stakeout of {id} has been modified by {ctx.message.author.name} to remove {key}.')
        else:
            data["factions"][str(id)]["keys"].append(key)
            embed.description = f'{key} has been added to the triggers of {data["factions"][str(id)]["name"]}.'
            await utils.log(ctx, "Faction Stakeout Modified", f'The stakeout of {id} has been modified by '
                                                              f'{ctx.message.author.name} to add {key}.')
            self.logger.info(f'The stakeout of {id} has been modified by {ctx.message.author.name} to add {key}.')

        dbutils.write("stakeouts", data)

        await ctx.send(embed=embed)

    @commands.command()
    async def lsfactions(self, ctx):
        data = dbutils.read("stakeouts")

        embed = discord.Embed()
        embed.title = "Faction Stakeouts"
        embed.description = f'Quantity: {len(data["factions"])}'

        factioncounter = 0
        pages = []

        for faction in data["factions"].values():
            embed.add_field(name=faction["name"],
                            value=f'Watched Keys: {"None" if faction["keys"] == [] else ", ".join(faction["keys"])}',
                            inline=False)

            if factioncounter % 25 == 0 and factioncounter != 0:
                factioncounter += 1
                pages.append(embed)
                embed = discord.Embed()
                embed.description = f'Quantity: {len(data["factions"])}'
                break
            else:
                factioncounter += 1
        else:
            if len(pages) == 0:
                pages.append(embed)

        for embed in pages:
            embed.description = f'Quantity: {len(data["factions"])}'

        message = await ctx.send(embed=pages[0])
        await message.add_reaction('⏮')
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        await message.add_reaction('⏭')

        def check(reaction, faction):
            return faction == ctx.author

        i = 0
        reaction = None

        while True:
            if str(reaction) == '⏮':
                i = 0
                await message.edit(embed=pages[i])
            elif str(reaction) == '◀':
                if i > 0:
                    i -= 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == '▶':
                if i < len(pages) - 1:
                    i += 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == '⏭':
                i = len(pages) - 1
                await message.edit(embed=pages[i])

            try:
                reaction, faction = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                await message.remove_reaction(reaction, faction)
            except:
                break

        await message.clear_reactions()
        await message.delete()
