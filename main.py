# Mysterious Stranger rewrite: main

import asyncio
import discord
import sqlite3
import datetime
import calendar
import pytz
import math
import random
import sys
import os
import importlib

# custom modules:
import admin
import maintenance
import settings
import study
import game
dynamic_modules = [admin, maintenance, settings, study, game]


client = settings.client

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    
    trigger = settings.trigger(message.guild)
    
    if message.content.startswith(trigger):
        command = message.content.split(" ")
        command[0] = command[0][1:]
        if command[0].lower() == 'hello':
            if len(command) > 1:
                if command[1].lower() == 'help':
                    await message.channel.send('```Say hi to the bot! It will say hi back :\).\n\nAvailable parameters: help```')
                else:
                    await message.channel.send('```Unrecognized parameter. Available parameters:\n  help```')
            else:
                msg = 'Hello {0.author.mention}'.format(message)
                await message.channel.send(msg)
                
        if command[0].lower() == 'commands':
            if len(command) > 1:
                if command[1].lower() == 'help':
                    await message.channel.send('```Displays a list of currently available commands for the bot.\n\nAvailable parameters: help```')
                
                else:
                    await message.channel.send('```Unrecognized parameter. Available parameters:\n  help```')
            else:
                await message.channel.send('```Here are the commands the bot currently supports:\n  %shello\n  %sinitialize\n  %saddme\n  %stimezone\n  %smarkme\n  %sdidistudy\n  %sstreak\n  %sleaderboard\n  %scalendar\n  %scolor\n  %scommands\n\n All commands include the "help" parameter that explains their use.```'.replace("%s", settings.trigger(message.guild)))
        
        if command[0].lower() == 'reload':
            if message.author.id == settings.owner:
                if len(command) > 1:
                    try:
                        importlib.reload(command[1])
                    except:
                        await message.channel.send('```Unknown module```')
                    
                else:
                    try:
                        importlib.reload(admin)
                        importlib.reload(maintenance)
                        importlib.reload(settings)
                        importlib.reload(study)
                        importlib.reload(game)
                        
                        await message.channel.send('```All modules reloaded successfully.```')
                    except:
                        await message.channel.send('```Module reload failed.```')
                    
        
        if command[0].lower() == 'shutdown':
            if message.author.id == settings.owner:
                await message.channel.send('```Disconnecting the bot.```')
                
                await client.logout()
                await client.close()
                sys.exit()
            else:
                await message.channel.send('```Only the bot owner can shut me down, sorry.```')
        
        if 'maintenance' in sys.modules:
            await maintenance.commands(message)
        
        if 'admin' in sys.modules:
            await admin.commands(message)
        
        if 'study' in sys.modules:
            await study.commands(message)
            
        if 'game' in sys.modules:
            await game.commands(message)
        
    
@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == client.user:
        if user == client.user:
            return
            
        conn = sqlite3.connect(settings.database(reaction.message.guild))
        cursor = conn.cursor()                                 
        cursor.execute("SELECT user, type, data FROM commanddata WHERE message = ?", (reaction.message.id,))
        session = cursor.fetchone()
        conn.close()
        
        if session:
            if 'study' in sys.modules:
                await study.interactive_emotes(reaction, user, session)
            if 'game' in sys.modules:
                await game.interactive_emotes(reaction, user, session)


@client.event
async def on_message_delete(message):
    if message.author == client.user:
        return
    
    if 'admin' in sys.modules:
        await asyncio.sleep(1)
        await admin.logmessage(message, message)
        

@client.event
async def on_message_edit(before, after):
    if before.author == client.user:
        return
        
    if 'admin' in sys.modules:
        await asyncio.sleep(1)
        await admin.logmessage(before, after)

@client.event 
async def on_guild_role_create(role):
    if 'admin' in sys.modules:
        admin.colorcreate(role)
    
@client.event
async def on_guild_role_delete(role):
    if 'admin' in sys.modules:
        admin.colorremove(role)


@client.event
async def on_member_update(before, after):
    if 'admin' in sys.modules:
        admin.memberupdate(before, after)


@client.event 
async def on_member_join(member):
    if 'admin' in sys.modules:
        await admin.newmember(member)
        
@client.event
async def on_member_remove(member):
    if 'admin' in sys.modules:
        await admin.memberleave(member)
        
@client.event
async def on_guild_join(guild):
    if 'maintenance' in sys.modules:
        maintenance.initialize(guild)
    
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------------')
    
    for server in client.guilds:        
        if not os.path.isfile(settings.database(server)):
            print('Bot has no database established for server ' + server.name)

client.run(settings.token)
