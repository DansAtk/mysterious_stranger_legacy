import asyncio
import discord
import sqlite3
import datetime
import calendar
import pytz
import math
import random
import json
import os

import settings

client = settings.client

async def findmember(guild, query):
    
    #Returns a list of all users in the server with names or nicknames matching the search query. If none are found returns an empty list.

    conn = sqlite3.connect(settings.database(guild))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username LIKE ? OR nickname LIKE ?", ('%' + query + '%', '%' + query + '%'))
    usersearch = cursor.fetchall()
    conn.close()
                    
    return usersearch
    
async def checkdate(datestring, today):
    
    #Returns a datetime object if the string is a valid date, and an integer code specifying invalid values if not. Adjusted for different time zones by giving the present time in the time zone of choice.
    
    validity = 0
    
    datevalues = datestring.split("-")
    
    if len(datevalues) == 1:
        year = today.year
        month = today.month
        try:
            day = int(datestring)
        except ValueError:
            validity += 1

    elif len(datevalues) == 2:
        year = today.year
        try:
            month = int(datevalues[0])
        except ValueError:
            validity += 2
        try:
            day = int(datevalues[1])
        except ValueError:
            validity += 1

    elif len(datevalues) == 3:
        try:
            year = int(datevalues[0])
        except ValueError:
            validity += 4
        try:
            month = int(datevalues[1])
        except ValueError:
            validity += 2
        try:
            day = int(datevalues[2])
        except ValueError:
            validity += 1
    
    if validity == 0:
        if year >= (today.year - 100) and year <= (today.year + 100):
            if month > 0 and month <= 12:
                monthlen = calendar.monthrange(year, month)
                if day > 0 and day <= monthlen[1]:
                    try:
                        validity = datetime.date(year, month, day)
                    except ValueError:
                        validity = 8
                else:
                    validity = 1
            else:
                validity = 2
        else:
            validity = 4
    
    print(type(validity))
    return validity

  
async def interactive_emote(reaction, user, session):
    emoji_left = '\u2B05'
    emoji_right = '\u27A1'
        
    if user.id == int(session[0]) and session[1] == 'calendar':
        conn = sqlite3.connect(settings.database(reaction.message.guild))
        cursor = conn.cursor()
        
        textdate = session[2].split("-")
        
        if reaction.emoji == emoji_left:
            try:
                datedate = datetime.date(int(textdate[0]), int(textdate[1]) - 1, 1)
            except ValueError:
                datedate = datetime.date(int(textdate[0]) - 1, 12, 1)
        
        elif reaction.emoji == emoji_right:
            try:
                datedate = datetime.date(int(textdate[0]), int(textdate[1]) + 1, 1)
            except ValueError:
                datedate = datetime.date(int(textdate[0]) + 1, 1, 1)
    
        else:
            return
    
        newcalendar = drawcalendar(user, reaction.message, datedate)
        
        cursor.execute("UPDATE commanddata SET data = ? WHERE message = ?", (datedate.strftime('%Y-%m-%d'), reaction.message.id))
        
        sent = await reaction.message.edit(content=newcalendar)

        await reaction.message.clear_reactions()
        emoji = '\u2B05'
        await reaction.message.add_reaction(emoji)
        emoji = '\u27A1'
        await reaction.message.add_reaction(emoji)
    
        conn.commit()
        conn.close()
        
    elif session[1] == 'kanagame':
        return