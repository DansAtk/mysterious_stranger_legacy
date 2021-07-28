import asyncio
import discord
import sqlite3
import datetime
import calendar
import pytz
import math
import random

import settings
import dotd
client = settings.client

cooldown = datetime.timedelta(seconds=10)

async def commands(message):
    command = message.content.split(" ")
    command[0] = command[0][1:]
    
    if command[0].lower() == 'game':
        if len(command) > 1:
            if command[1].lower() == 'help':
                reply = 'Bit bite oot ouch owie.\n\nAvailable parameters: help'
                
            elif command[1].lower() == 'ready':
                readyrole = discord.utils.get(message.guild.roles, name='survivor')
                if len(command) > 2:
                    if command[2].lower() == 'all':
                        for player in message.guild.members:
                            if player.id != client.user.id:
                                userroles = player.roles
                                if readyrole not in userroles:
                                    await player.add_roles(readyrole, atomic=True)
                        
                        reply = 'Everyone is ready.'            
                        
                else:
                    if gamestatus(1, message.guild) == 0:
                        userroles = message.author.roles
                    
                        if readyrole in userroles:
                            reply = 'You are already readied.'
                            
                        else:
                            reply = 'You are ready.'
                            await message.author.add_roles(readyrole, atomic=True)
                    else:
                        reply = 'A game is already in play. Please wait until the current game has ended before readying for the next one.'
                    
            elif command[1].lower() == 'unready':
                readyrole = discord.utils.get(message.guild.roles, name='survivor')
                userroles = message.author.roles
                
                if gamestatus(1, message.guild) == 1:
                    if readyrole in userroles:
                        reply = 'No quittin!'
                        
                    else:
                        reply = 'You\'re not even in the game anyways.'
                    
                    
                else:
                    if readyrole in userroles:
                        reply = 'Unreadying you.'
                        await message.author.remove_roles(readyrole, atomic=True)
                        
                    else:
                        reply = 'You weren\'t ready anyways.'
                    
            elif command[1].lower() == 'start':
                if message.author.permissions_in(message.channel).administrator:
                    if len(command) > 2:
                        if command[2].lower() == 'dotd':
                            if gamestatus(1, message.guild) == 0:
                                reply = await dotd.start(message)
                                
                            else:
                                if gamestatus(1, message.guild) == 1:
                                    reply = 'A game is already running.'
                                else:
                                    reply = 'Something went wrong.'
                        else:
                            reply = 'Unrecognized game mode.'
                    else:
                        reply = 'Please specify a game mode.'
                    
            elif command[1].lower() == 'stop':
                if message.author.permissions_in(message.channel).administrator:
                    if len(command) > 2:
                        if command[2].lower() == 'dotd':
                            if gamestatus(1, message.guild) > 0:
                                await end_game(1, message.guild)

                                reply = 'Stopping game...'
                            else:
                                reply = 'That game is not currently running.'
                        else:
                            reply = 'Unrecognized game mode.'
                    else:
                        reply = 'Please specify a game mode.'
            elif command[1].lower() == 'begin':
                reply = 'Please enter your credit card information to begin.'
            
            else:
                reply = 'Unrecognized parameter.'
                
            
        else:
            reply = 'No parameter specified.'
        
        await message.channel.send(reply)
    
    else:
        await dotd.commands(message)
        
def gamestatus(gameid, guild):
    conn = sqlite3.connect(settings.database(guild))
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM gamedata WHERE type = 'gamemode' AND data LIKE ?", (str(gameid) + ';%',))
    gamedata = cursor.fetchone()
    gamestatus = gamedata[0].split(";")[2]
    
    reply = 2
    
    if gamestatus == '1':
        reply = 1
        
    else:
        reply = 0
    
    conn.close()
    
    return reply
    
    
async def end_game(gameid, guild):
    survivor = discord.utils.get(guild.roles, name='survivor')
    undead = discord.utils.get(guild.roles, name='undead')
    
    for player in guild.members:
        userroles = player.roles
            
        if survivor in userroles:
            await player.remove_roles(survivor, atomic=True)
            
        if undead in userroles:
            await player.remove_roles(undead, atomic=True)
                        
    conn = sqlite3.connect(settings.database(guild))
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM gamedata WHERE type = 'gamemode' AND data LIKE ?", (str(gameid) + ';%',))
    gamedata = cursor.fetchone()
    gamedata = gamedata[0].split(";")
    gamedata[2] = '0'
    
    for item in gamedata[1:]:
        gamedata[0] += ';' + str(item)
    
    cursor.execute("UPDATE gamedata SET data = ? WHERE type = 'gamemode' AND data LIKE ?", (str(gamedata[0]), str(gameid) + ';%'))
            
    conn.commit()
    conn.close()
    
async def interactive_emotes(reaction, user, session):
    if session[1] == 'lootdrop':
        survivor = discord.utils.get(reaction.message.guild.roles, name='survivor')

        survivors = survivor.members
        
        if user in survivors:
            await reaction.message.delete()
        
            reply = dotd.drop_item(user, session[2], reaction.message.guild)
        
            await reaction.message.channel.send(reply)
            
            conn = sqlite3.connect(settings.database(reaction.message.guild))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM commanddata WHERE type = 'lootdrop' and message = ?", (reaction.message.id, ))
            conn.commit()
            conn.close()
            
    elif session[1] == 'death':
        emoji_syringe = '\U0001F489'
        if reaction.emoji == emoji_syringe:
            if session[0] == user.id:
                conn = sqlite3.connect(settings.database(reaction.message.guild))
                cursor = conn.cursor()                                 
                cursor.execute("UPDATE commanddata SET data = '1' WHERE message = ?", (reaction.message.id,))
                conn.commit()
                conn.close()
                
                await reaction.message.delete()

        
def initialize(guild):
    conn = sqlite3.connect(settings.database(guild))
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE gamedata(id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, data TEXT, isactive INTEGER DEFAULT '0')")
    print('\'gamedata\' table created.')
    cursor.execute("INSERT INTO gamedata(type, data) VALUES (?, ?)", ('weapon','nothing;0'))
    print('Null weapon placed in gamedata.')
    cursor.execute("INSERT INTO gamedata(type, data) VALUES (?, ?)", ('gamemode','1;dotd;0;0'))
    print('DOTD gamemode placed in gamedata.')
    
    conn.commit()
    conn.close()

