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

# custom modules:
import admin
import maintenance
import settings
import study
import game

client = settings.client
dbversion = '1.00'

async def commands(message):
    if message.author.permissions_in(message.channel).administrator:
        command = message.content.split(" ")
        command[0] = command[0][1:]
        
        if command[0].lower() == 'initialize':
            if len(command) > 1:
                if command[1].lower() == 'help':
                    await message.channel.send('```Creates a database for the current server and imports all members.\n\nAvailable parameters: help```')
                
                else:
                    await message.channel.send('```Unrecognized parameter. Available parameters:\n  help```')
            else:
                result = initialize(message.guild)
                
                if result:
                    await message.channel.send('```A database already exists for this server.```')
                else:
                    await message.channel.send('```Initialization complete.```')
                    
                
        if command[0].lower() == 'clear':
            if len(command) > 1:
                if command[1].lower() == 'help':
                    reply = '```Temporary tool used to clear the interactive message cache.\n\nAvailable parameters: help```'
                
                else:
                    reply = '```Unrecognized parameter. Available parameters:\n  help```'
                    
            else:
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM commanddata")
                conn.commit()
                conn.close()
                reply = '```Table "commanddata" has been cleared.```'
                
            await message.channel.send(reply)
            
def initialize(guild):
    if os.path.isfile(settings.database(guild)):
        return 1
        
    else:  
        members = guild.members
        conn = sqlite3.connect(settings.database(guild))
        print('Database file created at ' + settings.database(guild))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE config(id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT)")
        print('\'config\' table created.')
        cursor.execute("INSERT INTO config(key, value) VALUES (?, ?)", ('dbversion', dbversion))
        cursor.execute("INSERT INTO config(key, value) VALUES (?, ?)", ('trigger', '~'))
        cursor.execute("INSERT INTO config(key, value) VALUES (?, ?)", ('cheer', '\U0001F44D'))
        print('\'config\' table populated.')
        cursor.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, nickname TEXT, isbanned INTEGER DEFAULT '0', active INTEGER)")
        print('\'users\' table created.')
        
        for x in members:

            cursor.execute("INSERT INTO users(id, username, nickname, active) VALUES (?, ?, ?, ?)", (x.id, x.name, x.nick, 1))
                
        print('\'users\' table populated.')
        
        cursor.execute("CREATE TABLE commanddata(message INTEGER, type TEXT, user INTEGER, data TEXT)")
        print('\'commanddata\' table created.')
        
        conn.commit()
        conn.close()
        
        if 'study' in sys.modules:
            study.initialize(guild)
            
        
        if 'admin' in sys.modules:
            admin.initialize(guild)
        
        
        if 'game' in sys.modules:
            game.initialize(guild)
            
        return 0