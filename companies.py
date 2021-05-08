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


class Companies(commands.Cog):
    def __init__(self, logger, bot):
        self.logger = logger
        self.bot = bot

        self.update_companies.start()

    @tasks.loop(minutes=1)
    async def update_companies(self):
        start = time.time()

        async def get(url, session):
            async with session.get(url) as response:
                return await response.read()

        data = dbutils.read("stakeouts")
        tasks = []
        async with ClientSession() as session:
            for company in data["companies"]:
                task = asyncio.ensure_future(get(f'https://api.torn.com/company/{company}?selections='
                                                 f'&key={utils.key()}', session))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            responses = [json.loads(response.decode('UTF-8')) for response in responses]

            for company in responses:
                keys = data["companies"][str(company["ID"])]["keys"]
                channel = discord.utils.get(self.bot.guilds[0].channels, name=f'company-{company["ID"]}')

                if "members" in keys and data["companies"][str(company["ID"])]["members"] != company["members"]:
                    for memberid, member in data["companies"][str(company["ID"])]["members"].items():
                        if memberid not in company["members"]:
                            embed = discord.Embed()
                            embed.title = "Member Left"
                            embed.description = f'Member {member["name"]} has left the staked out company ' \
                                                f'{company["name"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                    for memberid, member in company["members"].items():
                        if memberid not in data["factions"][str(company["ID"])]["members"]:
                            embed = discord.Embed()
                            embed.title = "Member Joined"
                            embed.description = f'Member {member["name"]} has joined the staked out company ' \
                                                f'{company["name"]}.'
                            embed.timestamp = datetime.datetime.utcnow()
                            await channel.send(embed=embed)

                data["companies"][str(company["ID"])] = company
                data["companies"][str(company["ID"])]["keys"] = keys
            dbutils.write("stakeouts", data)

        self.logger.info(f'Auto-updater for companies run in {time.time() - start} seconds.')

    @commands.command()
    async def initcompany(self, ctx, id: int):
        data = dbutils.read("stakeouts")

        if id in data["companies"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Company ID {id} is already being staked out.'
            await ctx.send(embed=embed)
            raise Exception

        request = requests.get(f'https://api.torn.com/company/{id}?selections=&key={utils.key()}')

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

        data["companies"][str(id)] = request.json()
        data["companies"][str(id)]["keys"] = []
        dbutils.write("stakeouts", data)

        await ctx.guild.create_text_channel(
            f'company-{request.json()["ID"]}',
            category=discord.utils.get(ctx.guild.categories, name=dbutils.get("settings", "stakeout"))
        )

        embed = discord.Embed()
        embed.title = "Company Stakeout Added"
        embed.description = f'The stakeout of company ID {id}, {request.json()["name"]}, has been added.'
        await ctx.send(embed=embed)

        await utils.log(ctx, "Company Stakeout Added", f'The stakeout of {id} has been added by '
                                                       f'{ctx.message.author.name}.')
        self.logger.info(f'The stakeout of company {id} has been added by {ctx.message.author.name}.')

    @commands.command()
    async def rmcompany(self, ctx, id: int):
        data = dbutils.read("stakeouts")

        if str(id) not in data["companies"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Company ID {id} is not currently being staked out.'
            await ctx.send(embed=embed)
            return Exception

        channel = discord.utils.get(ctx.guild.channels, name=f'company-{data["companies"][str(id)]["ID"]}')
        await channel.delete()

        data["companies"].pop(str(id))
        dbutils.write("stakeouts", data)

        try:
            embed = discord.Embed()
            embed.title = "Company Stakeout Removed"
            embed.description = f'The stakeout of company ID {id} has been removed.'
            await ctx.send(embed=embed)
        except:
            pass

        await utils.log(ctx, "Company Stakeout Removed", f'The stakeout of {id} has been removed by '
                                                         f'{ctx.message.author.name}.')
        self.logger.info(f'The stakeout of company {id} has been removed by {ctx.message.author.name}.')

    @commands.command()
    async def editcompany(self, ctx, id: int, key: str):
        data = dbutils.read("stakeouts")
        valid_keys = ["members"]

        if str(id) not in data["companies"]:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = f'Company {id} is not currently being staked out.'
            await ctx.send(embed=embed)
            return Exception

        if key not in valid_keys:
            embed = discord.Embed()
            embed.title = "Invalid Key"
            embed.description = f'The given key, {key}, is not valid. Please make sure that you\'r using a valid key,'
            await ctx.send(embed=embed)
            return Exception

        embed = discord.Embed()
        embed.title = "Company Stakeout Modified"

        if key in data["companies"][str(id)]["keys"]:
            data["companies"][str(id)]["keys"].pop(key)
            embed.description = f'{key} has been removed from the triggers of {data["companies"][str(id)]["name"]}.'
            await utils.log(ctx, "Company Stakeout Modified", f'The stakeout of {id} has been modified by '
                                                              f'{ctx.message.author.name} to remove {key}.')
            self.logger.info(f'The stakeout of {id} has been modified by {ctx.message.author.name} to remove {key}.')
        else:
            data["companies"][str(id)]["keys"].append(key)
            embed.description = f'{key} has been added to the triggers of {data["companies"][str(id)]["name"]}.'
            await utils.log(ctx, "Company Stakeout Modified", f'The stakeout of {id} has been modified by '
                                                              f'{ctx.message.author.name} to add {key}.')
            self.logger.info(f'The stakeout of {id} has been modified by {ctx.message.author.name} to add {key}.')

        dbutils.write("stakeouts", data)

        await ctx.send(embed=embed)

    @commands.command()
    async def lscompanies(self, ctx):
        data = dbutils.read("stakeouts")

        embed = discord.Embed()
        embed.title = "Company Stakeouts"
        embed.description = f'Quantity: {len(data["companies"])}'

        companycounter = 0
        pages = []

        for company in data["companies"].values():
            embed.add_field(name=company["name"],
                            value=f'Watched Keys: {"None" if company["keys"] == [] else ", ".join(company["keys"])}',
                            inline=False)

            if companycounter % 25 == 0 and companycounter != 0:
                companycounter += 1
                pages.append(embed)
                embed = discord.Embed()
                embed.description = f'Quantity: {len(data["companies"])}'
                break
            else:
                companycounter += 1
        else:
            if len(pages) == 0:
                pages.append(embed)

        for embed in pages:
            embed.description = f'Quantity: {len(data["companies"])}'

        message = await ctx.send(embed=pages[0])
        await message.add_reaction('⏮')
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        await message.add_reaction('⏭')

        def check(reaction, company):
            return company == ctx.author

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
                reaction, company = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                await message.remove_reaction(reaction, company)
            except:
                break

        await message.clear_reactions()
        await message.delete()
