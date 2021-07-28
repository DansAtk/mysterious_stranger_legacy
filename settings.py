import discord
import sqlite3
import os

# Bot token here
token = ''

# Bot owner ID here
owner = 

intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Local path to bot directory here
botpath = ''

datapath = 'data/'

pathtodb = datapath + '%s.db'

backuppath = datapath + 'backup/'

def trigger(guild):
    if os.path.isfile(database(guild)):
        try:
            conn = sqlite3.connect(database(guild))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = 'trigger'")
            trigger = cursor.fetchone()
            conn.close()
        except:
            trigger = ('!',)
            
    else:
        trigger = ('!',)
        
    return trigger[0]
    
def cheer(guild):
    cheer = 0
    if os.path.isfile(database(guild)):
        try:
            conn = sqlite3.connect(database(guild))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = 'cheer'")
            cheer = cursor.fetchone()
            conn.close()
        except:
            cheer = (0,)
    else:
        cheer = (0,)
    
    if cheer:
        return cheer[0]
    else:
        return 0


def database(guild):
    database = pathtodb % (str(guild.id))
    return database
    
def backup(guild):
    backup = backuppath + str(guild.id)
    return backup
