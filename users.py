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


class Users(commands.Cog):
    def __init__(self, logger, bot):
        self.logger = logger
        self.bot = bot

        self.update_users.start()

    @tasks.loop(minutes=1)
    async def update_users(self):
        start = time.time()

        async def get(url, session):
            async with session.get(url) as response:
                return await response.read()

        data = dbutils.read("stakeouts")
        tasks = []
        async with ClientSession() as session:
            for user in data["users"]:
                task = asyncio.ensure_future(get(f'https://api.torn.com/user/{user}?selections=&key={utils.key()}',
                                                 session))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            responses = [json.loads(response.decode('UTF-8')) for response in responses]

            for user in responses:
                keys = data["users"][str(user["player_id"])]["keys"]
                channel = discord.utils.get(self.bot.guilds[0].channels, name=f'user-{user["name"]}')

                if "level" in keys and data["users"][str(user["player_id"])]["level"] != user["level"]:
                    embed = discord.Embed()
                    embed.title = "Level Change"
                    embed.description = f'The level of staked out user {user["name"]} has changed from ' \
                                        f'{data["users"][str(user["player_id"])]["level"]} to {user["level"]}.'
                    embed.timestamp = datetime.datetime.utcnow()
                    await channel.send(embed=embed)
                if "okay" in keys and data["users"][str(user["player_id"])]["status"]["state"] == "Hospital" and \
                        user["status"]["state"] == "Okay":
                    embed = discord.Embed()
                    embed.title = "Status Change"
                    embed.description = f'The status of staked out user {user["name"]} has changed from ' \
                                        f'{data["users"][str(user["player_id"])]["status"]["state"]} to ' \
                                        f'{user["status"]["state"]}.'
                    embed.timestamp = datetime.datetime.utcnow()
                    await channel.send(embed=embed)
                if "landed" in keys and data["users"][str(user["player_id"])]["status"]["state"] == "Travelling" \
                        and "In" in user["status"]["state"]:
                    embed = discord.Embed()
                    embed.title = "Status Change"
                    embed.description = f'The status of staked out user {user["name"]} has changed from ' \
                                        f'{data["users"][str(user["player_id"])]["status"]["state"]} to ' \
                                        f'{user["status"]["state"]}.'
                    embed.timestamp = datetime.datetime.utcnow()
                    await channel.send(embed=embed)
                if "online" in keys and data["users"][str(user["player_id"])]["last_action"]["status"] in \
                        ("Offline", "Idle") and user["last_action"]["status"] == "Online":
                    embed = discord.Embed()
                    embed.title = "Status Change"
                    embed.description = f'The status of staked out user {user["name"]} has changed from ' \
                                        f'{data["users"][str(user["player_id"])]["last_action"]["status"]} to ' \
                                        f'{user["last_action"]["status"]}.'
                    embed.timestamp = datetime.datetime.utcnow()
                    await channel.send(embed=embed)
                if "offline" in keys and data["users"][str(user["player_id"])]["last_action"]["status"] in \
                        ("Online", "Idle") and user["last_action"]["status"] in ("Offline", "Idle"):
                    if user["last_action"]["status"] == "Idle" and \
                            datetime.datetime.now(datetime.timezone.utc).timestamp() - \
                            user["last_action"]["timestamp"] < 300:
                        continue

                    if user["last_action"]["status"] == "Idle" and \
                            data["users"][str(user["player_id"])]["last_action"]["status"] == "Idle":
                        continue

                    embed = discord.Embed()
                    embed.title = "Status Change"
                    embed.description = f'The status of staked out user {user["name"]} has changed from ' \
                                        f'{data["users"][str(user["player_id"])]["last_action"]["status"]} to ' \
                                        f'{user["last_action"]["status"]}.'
                    embed.timestamp = datetime.datetime.utcnow()
                    await channel.send(embed=embed)
                data["users"][str(user["player_id"])] = user
                data["users"][str(user["player_id"])]["keys"] = keys
            dbutils.write("stakeouts", data)

        self.logger.info(f'Auto-updater for users run in {time.time() - start} seconds.')

    @commands.command()
    async def inituser(self, ctx, id: int):
        data = dbutils.read("stakeouts")

        if id in data["users"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'User ID {id} is already being staked out.'
            await ctx.send(embed=embed)
            raise Exception

        request = requests.get(f'https://api.torn.com/user/{id}?selections=&key={utils.key()}')

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

        data["users"][str(id)] = request.json()
        data["users"][str(id)]["keys"] = []
        dbutils.write("stakeouts", data)

        await ctx.guild.create_text_channel(
            f'user-{request.json()["name"]}',
            category=discord.utils.get(ctx.guild.categories, name=dbutils.get("settings", "stakeout"))
        )

        embed = discord.Embed()
        embed.title = "User Stakeout Added"
        embed.description = f'The stakeout of user ID {id}, {request.json()["name"]}, has been added.'
        await ctx.send(embed=embed)

        await utils.log(ctx, "User Stakeout Added", f'The stakeout of {id} has been added by '
                                                    f'{ctx.message.author.name}.')
        self.logger.info(f'The stakeout of user {id} has been added by {ctx.message.author.name}.')

    @commands.command()
    async def rmuser(self, ctx, id: int):
        data = dbutils.read("stakeouts")

        if str(id) not in data["users"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'User {id} is not currently being staked out.'
            await ctx.send(embed=embed)
            return Exception

        channel = discord.utils.get(ctx.guild.channels, name=f'user-{data["users"][str(id)]["name"]}')
        await channel.delete()

        data["users"].pop(str(id))
        dbutils.write("stakeouts", data)

        try:
            embed = discord.Embed()
            embed.title = "User Stakeout Removed"
            embed.description = f'The stakeout of user ID {id} has been removed.'
            await ctx.send(embed=embed)
        except:
            pass

        await utils.log(ctx, "User Stakeout Removed", f'The stakeout of {id} has been removed by '
                                                     f'{ctx.message.author.name}.')
        self.logger.info(f'The stakeout of user {id} has been removed by {ctx.message.author.name}.')

    @commands.command()
    async def edituser(self, ctx, id:int, key: str):
        data = dbutils.read("stakeouts")
        valid_keys = ["level", "okay", "landed", "online", "offline"]

        if str(id) not in data["users"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'User {id} is not currently being staked out.'
            await ctx.send(embed=embed)
            return Exception

        if key not in valid_keys:
            embed = discord.Embed()
            embed.title = "Invalid Key"
            embed.description = f'The given key, {key}, is not valid. Please make sure that you\'r using a valid key,'
            await ctx.send(embed=embed)
            return Exception

        embed = discord.Embed()
        embed.title = "User Stakeout Modified"

        if key in data["users"][str(id)]["keys"]:
            data["users"][str(id)]["keys"].pop(key)
            embed.description = f'{key} has been removed from the triggers of {data["users"][str(id)]["name"]}.'
            await utils.log(ctx, "User Stakeout Modified", f'The stakeout of {id} has been modified by '
                                                           f'{ctx.message.author.name} to remove {key}.')
            self.logger.info(f'The stakeout of {id} has been modified by {ctx.message.author.name} to remove {key}.')
        else:
            data["users"][str(id)]["keys"].append(key)
            embed.description = f'{key} has been added to the triggers of {data["users"][str(id)]["name"]}.'
            await utils.log(ctx, "User Stakeout Modified", f'The stakeout of {id} has been modified by '
                                                           f'{ctx.message.author.name} to add {key}.')
            self.logger.info(f'The stakeout of {id} has been modified by {ctx.message.author.name} to add {key}.')

        dbutils.write("stakeouts", data)

        await ctx.send(embed=embed)

    @commands.command()
    async def lsusers(self, ctx):
        data = dbutils.read("stakeouts")

        embed = discord.Embed()
        embed.title = "User Stakeouts"
        embed.description = f'Quantity: {len(data["users"])}'

        usercounter = 0
        pages = []

        for user in data["users"].values():
            embed.add_field(name=user["name"],
                            value=f'Watched Keys: {"None" if user["keys"] == [] else ", ".join(user["keys"])}',
                            inline=False)

            if usercounter % 25 == 0 and usercounter != 0:
                usercounter += 1
                pages.append(embed)
                embed = discord.Embed()
                embed.description = f'Quantity: {len(data["users"])}'
                break
            else:
                usercounter += 1
        else:
            if len(pages) == 0:
                pages.append(embed)

        for embed in pages:
            embed.description = f'Quantity: {len(data["users"])}'

        message = await ctx.send(embed=pages[0])
        await message.add_reaction('⏮')
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        await message.add_reaction('⏭')

        def check(reaction, user):
            return user == ctx.author

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
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                await message.remove_reaction(reaction, user)
            except:
                break

        await message.clear_reactions()
        await message.delete()
