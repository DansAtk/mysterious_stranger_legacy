import asyncio
import discord
import sqlite3
import datetime
import calendar
import pytz
import math
import random
import os

import settings
client = settings.client

async def commands(message):
    command = message.content.split(" ")
    command[0] = command[0][1:]
    
    if command[0].lower() == 'trigger':
        if message.author.permissions_in(message.channel).administrator:
            
            if command[1].lower() == 'help':
                await message.channel.send(command_ref["trigger"]["help"])
            else:
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("UPDATE config SET value = ? WHERE key = 'trigger'", (command[1],))
                conn.commit()
                conn.close()
            
                await message.channel.send(command_ref["trigger"]["success"] % command[1])
            
    
    if command[0].lower() == 'dbcheck':
        if message.author.permissions_in(message.channel).administrator:
            if len(command) > 1:
                if command[1].lower() == 'all':
                    reply = '```Database status for joined servers:\n'
                    for server in client.guilds:
                        reply += '\t' + '{:32}'.format(server.name + ':')
                        if os.path.isfile(settings.database(server)):
                            try:
                                conn = sqlite3.connect(settings.database(server))
                                cursor = conn.cursor()
                                cursor.execute("SELECT value FROM config WHERE key = 'dbversion'")
                                version = cursor.fetchone()
                                conn.close()
                            
                                if version:
                                    reply += 'Version ' + str(version[0]) + '\n'
                                else:
                                    reply += 'Version 0.9\n' 
                            except:
                                reply += 'Legacy\n'
                        else:
                            reply += 'Not found\n'
                            
                    reply += '```'
                    
                else:
                    reply = '```Unrecognized parameter.```'

            else:
                reply = '```Database status for this server:\t'
                
                if os.path.isfile(settings.database(message.guild)):
                    try:
                        conn = sqlite3.connect(settings.database(message.guild))
                        cursor = conn.cursor()
                        cursor.execute("SELECT value FROM config WHERE key = 'dbversion'")
                        version = cursor.fetchone()
                        conn.close()
                    
                        if version:
                            reply += 'Version ' + str(version[0])
                        else:
                            reply += 'Version 0.9' 
                    except:
                        reply += 'Legacy'
                else:
                    reply += 'Not found'
                
                reply += '```'
            
            await message.channel.send(reply)
    
    if command[0].lower() == 'defaultrole':
        if message.author.permissions_in(message.channel).administrator:
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = 'defaultrole'")
            results = cursor.fetchone()
            
            if len(command) > 1:
                if command[1][0] == '"':
                    nameparse = message.content.split("\"")
                    
                    rolename = nameparse[1]
                    
                    if len(command) > 2 and len(nameparse) > 2:
                        command[2] = nameparse[2][1:]
                else:
                    rolename = command[1]
                
                role = discord.utils.get(message.guild.roles, name=rolename)
                
                
                if role:
                    if results:
                        cursor.execute("UPDATE config SET value = ? WHERE key = 'defaultrole'", (role.id,))
                            
                        reply = '```Default role updated to ' + role.name + '```'
                            
                    else:
                        cursor.execute("INSERT INTO config(key, value) VALUES (?, ?)", ('defaultrole', role.id))
                        
                        reply = '```Default role set to ' + role.name + '```'
                else:
                    if len(command) > 2:
                        if command[2] == 'force':
                            role = await message.guild.create_role(name=rolename)
                            
                            if results:
                                cursor.execute("UPDATE config SET value = ? WHERE key = 'defaultrole'", (role.id,))
                                
                            else:
                                cursor.execute("INSERT INTO config(key, value) VALUES (?, ?)", ('defaultrole', role.id))
                            
                            reply = '```Role ' + role.name + ' created and set as default.```'
                            
                        else:
                            reply = '```Unknown parameter.```'
                    
                    else:
                        reply = '```Role not found.```'
                    
                conn.commit()
                conn.close()
            
            else:
            
                if results:
                    currentrole = discord.utils.get(message.guild.roles, id=int(results[0]))
                    
                    if currentrole:
                        reply = '```The default role is currently set to ' + currentrole.name + '.```'
                    
                    else:
                        reply = '```No default role currently set!```'
                else:
                    reply = '```No default role currently set!```'
                    
            await message.channel.send(reply)
    
    
    if command[0].lower() == 'rolefix':
        if message.author.permissions_in(message.channel).administrator:
            for role in message.guild.roles:
                if role.color.value != 0 and not role.permissions.administrator:
                    await role.edit(permissions=role.permissions.none())
                    
    
    if command[0].lower() == 'colorrefresh':
        if message.author.permissions_in(message.channel).administrator:
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM colors")
            
            for role in message.guild.roles:
                color = role.color.value
                if color != 0:
                    if role.permissions == role.permissions.none():
                        cursor.execute("INSERT INTO colors(roleid, colorname, colorhex) VALUES (?, ?, ?)", (role.id, role.name, str(role.color)))
            
            conn.commit()
            conn.close()
            
            message.channel.send('Colors table updated.')
            
    
    if command[0].lower() == 'color':
        if len(command) > 1:
            if command[1].lower() == 'help':
                await message.channel.send('```Used to check and set your color on the server.\n\nAvailable parameters: help, stats```')
            
            elif command[1].lower() == 'create':
                if message.author.permissions_in(message.channel).administrator:
                    if len(command) == 4:
                        if len(command[3]) > 5 and len(command[3]) < 8:
                            if len(command[3]) == 6:
                                command[3] = '#' + command[3]
                                
                            conn = sqlite3.connect(settings.database(message.guild))
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM colors WHERE colorname LIKE ? OR colorhex = ?", (command[2], command[3]))
                            check = cursor.fetchone()
                            if check[0]:
                                await message.channel.send('```A color with that name or value already exists.```')
                                
                            else:
                                await message.guild.create_role(name=command[2], color=discord.Color(int(command[3][1:], 16)))
                                await message.channel.send('```New color "%s" (%s) was successfully created.```' % (command[2], command[3]))
                                
                            conn.close()
                        else:
                            await message.channel.send('```Color code not in correct format. Please specify color using HEX CODE(#000000) only.```')
                    else:
                        await message.channel.send('```Please give a name for the new color, and specify its value using HEX CODE(#000000).```')
            
            elif command[1].lower() == 'remove':
                if message.author.permissions_in(message.channel).administrator:
                    conn = sqlite3.connect(settings.database(message.guild))
                    cursor = conn.cursor()
                    cursor.execute("SELECT roleid, colorname FROM colors WHERE colorname LIKE ?", ('%' + command[2] + '%',))
                    checkresults = cursor.fetchall()
                    if len(checkresults) > 1:
                        replystring = '```More than one matching color found.\n\n'
                        for color in checkresults:
                            replystring = replystring + '    ' + color[1] + '\n'
                        
                        replystring += '```'
                        await message.channel.send(replystring)
                    
                    elif len(checkresults) == 1:
                                           
                        await discord.utils.get(message.guild.roles, id=checkresults[0][0]).delete()
                        
                        await message.channel.send('```Color "%s" was successfully deleted.```' % (checkresults[0][1]))
                        
                    else:
                        await message.channel.send('```No colors like "%s" found.```' % (command[2]))
                        
                    conn.close()
            
            
            elif command[1].lower() == 'stats':
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT colors.colorname, COUNT(users.id) FROM users JOIN colors ON users.color = colors.roleid GROUP BY colors.roleid")
                colorlist = cursor.fetchall()
                conn.close()
                
                reply = '```Number of users by color:\n'
                
                for row in colorlist:
                    reply += '\t' + '{:10}'.format(str(row[0]) + ' - ') + str(row[1]) + ' users\n'
                
                reply += '```'
                
                await message.channel.send(reply)
                
            elif command[1].lower() == 'list':
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT colorname FROM colors ORDER BY colorname")
                colorlist = cursor.fetchall()
                conn.close()
                
                reply = '```Colors currently active:'
                
                for row in colorlist:
                    reply += '\n\t' + row[0]
                    
                reply += '```'
                
                await message.channel.send(reply)
            
            else:
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                if command[1][0] == '#':
                    hexcode = command[1][1:]
                    cursor.execute("SELECT roleid, colorname FROM colors WHERE colorhex = ?", (hexcode,))
                    colorresults = cursor.fetchall()
                    if len(colorresults) == 1:
                        cursor.execute("SELECT users.color FROM users JOIN colors ON colors.roleid = users.color WHERE users.id = ?", (message.author.id,))
                        currentcolor = cursor.fetchone()
                        beforecolorrole = discord.utils.get(message.guild.roles, id=currentcolor[0])
                        aftercolorrole = discord.utils.get(message.guild.roles, id=colorresults[0][0])
                        
                        if currentcolor[0] != 0:
                            await message.author.remove_roles(beforecolorrole, atomic=True)
                        
                        await message.author.add_roles(aftercolorrole, atomic=True)
                        
                        await message.channel.send('```Color successfully changed to %s (%s)```' % (colorresults[0][1], command[1]))
                        cursor.execute("SELECT roleid FROM colors WHERE colorhex = ?", (str(aftercolorrole.color),))
                        newcolorid = cursor.fetchone()
                        
                    else:
                        await message.channel.send('```No colors with that value found.```')
                    
                else:
                    cursor.execute("SELECT roleid, colorname FROM colors WHERE colorname LIKE ?", ('%' + command[1] + '%',))
                    colorresults = cursor.fetchall()
                    if len(colorresults) > 0:
                        if len(colorresults) == 1:
                            cursor.execute("SELECT users.color FROM users JOIN colors ON colors.roleid = users.color WHERE users.id = ?", (message.author.id,))
                            currentcolor = cursor.fetchone()
                            aftercolorrole = discord.utils.get(message.guild.roles, id=colorresults[0][0])
                            
                            if currentcolor:
                                beforecolorrole = discord.utils.get(message.guild.roles, id=currentcolor[0])
                                await message.author.remove_roles(beforecolorrole, atomic=True)
                            
                            await message.author.add_roles(aftercolorrole, atomic=True)
                            cursor.execute("UPDATE users SET color = ? WHERE id = ?", (aftercolorrole.id, message.author.id))
 
                            await message.channel.send('```Color successfully changed to %s.```' % (colorresults[0][1]))
                        else:
                            colorsearch = '```Colors found like "' + command[1] + '":\n\n'
                            
                            for color in colorresults:
                                colorsearch = colorsearch + '        ' + color[1] + '\n'
                            
                            colorsearch += '```'
                            await message.channel.send(colorsearch)
                            
                    else:
                        await message.channel.send('```No color names like "%s" found.```' % (command[1]))
                
                conn.commit()
                conn.close()                
        else:
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT colors.colorname FROM users JOIN colors ON colors.roleid = users.color WHERE users.id = ?", (message.author.id,))
            usercolor = cursor.fetchone()
            if usercolor is None:
                await message.channel.send('```You have no color.```')
            else:
                await message.channel.send('```Your current color is %s.```' % (usercolor[0]))
            conn.close()    
    
    
    if command[0].lower() == 'echo':
        if message.author.permissions_in(message.channel).administrator:
            
            channelname = command[1]
            channel = discord.utils.get(message.guild.channels, name=channelname)
            
            if channel is None:
                reply = 'Channel not found!'
            else:
                replytext = ''
                for param in command[2:]:
                    replytext += ' ' + str(param)
                    
                command[2] = replytext.split('"')[1]
                reply = command[2]
                await channel.send(reply)
            

def colorcreate(role):
    if role.color.value != 0 and role.permissions.none():
        conn = sqlite3.connect(settings.database(role.guild))
        cursor = conn.cursor()                                 
        cursor.execute("INSERT INTO colors (roleid, colorname, colorhex) VALUES (?, ?, ?)", (role.id, role.name, str(role.color)))
        conn.commit()
        conn.close()
        
def colorremove(role):
    if role.color.value != 0 and role.permissions.none():
        conn = sqlite3.connect(settings.database(role.guild))
        cursor = conn.cursor()                                 
        cursor.execute("DELETE FROM colors WHERE roleid = ?", (role.id,))
        conn.commit()
        conn.close()


async def logmessage(message1, message2):
    logchannel = discord.utils.get(message1.guild.channels, name='chatlogs')
    if logchannel is None:
        overwrites = {
            message1.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            message1.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        logchannel = await message1.guild.create_text_channel('chatlogs', overwrites=overwrites)
        await asyncio.sleep(1)
    
    if message1.content == message2.content:
        if message1.content.startswith('https://tenor.com/view/'):
            return
        else:
            log = '```The following message has just been deleted by ' + message1.author.name + ' in #' + message1.channel.name + ':\n\t"' + message1.content + '"```'
    else:
        log = '```The following message has just been edited by ' + message1.author.name + ' in #' + message1.channel.name + ':\n\t'
        log += 'Before: "' + message1.content + '"\n\tAfter: "' + message2.content + '"```'
    await logchannel.send(log)
    

def memberupdate(before, after):
    if before.nick != after.nick:
        conn = sqlite3.connect(settings.database(after.guild))
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET nickname = ? WHERE id = ?", (after.nick, after.id))
        conn.commit()
        conn.close()
        
        
async def newmember(member):
    genchannel = discord.utils.get(member.guild.channels, name='general')
    logchannel = discord.utils.get(member.guild.channels, name='chatlogs')
    
    if logchannel is None:
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        logchannel = await member.guild.create_text_channel('chatlogs', overwrites=overwrites)
        await asyncio.sleep(1)
    
    
    await asyncio.sleep(1)
    conn = sqlite3.connect(settings.database(member.guild))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?", (member.id,))
    check = cursor.fetchone()
    
    cursor.execute("SELECT value FROM config WHERE key = 'defaultrole'")
    defaultrolecheck = cursor.fetchone()
    
    if defaultrolecheck:
        role = discord.utils.get(member.guild.roles, id=int(defaultrolecheck[0]))
        await member.add_roles(role, atomic=True)
    
    
    if check[0] > 0:
        cursor.execute("UPDATE users SET active = 1 WHERE id = ?", (member.id,))
        
        cursor.execute("SELECT colors.roleid FROM users JOIN colors ON colors.roleid = users.color WHERE users.id = ?", (member.id,))
        usercolor = cursor.fetchone()
        
        if usercolor is None:
            cursor.execute("SELECT roleid FROM colors")
            allcolors = cursor.fetchall()
            random.shuffle(allcolors)
            cursor.execute("UPDATE users SET color = ? WHERE id = ?", (allcolors[0][0], member.id))
            
            crole = discord.utils.get(member.guild.roles, id=allcolors[0][0])
            await member.add_roles(crole, atomic=True)
            
        else:
            crole = discord.utils.get(member.guild.roles, id=usercolor[0])
            await member.add_roles(crole, atomic=True)
            
        welcome = 'Welcome back, ' + member.name
        log = '```' + member.name + ' has just rejoined the server.```'

    else:
        cursor.execute("SELECT roleid FROM colors")
        allcolors = cursor.fetchall()
        random.shuffle(allcolors)
        cursor.execute("INSERT INTO users (id, username, color, active) VALUES (?, ?, ?, ?)", (member.id, member.name, allcolors[0][0], 1))
        crole = discord.utils.get(member.guild.roles, id=allcolors[0][0])
        await member.add_roles(crole, atomic=True)
        
        welcome = 'Welcome ' + member.name
        log = '```' + member.name + ' has just joined the server.```'

    conn.commit()
    conn.close()
    
    await genchannel.send(welcome)
    await logchannel.send(log)
        
async def memberleave(member):
    conn = sqlite3.connect(settings.database(member.guild))
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active = 0 WHERE id = ?", (member.id,))
    conn.commit()
    conn.close()
    

    logchannel = discord.utils.get(member.guild.channels, name='chatlogs')
    if logchannel is None:
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        logchannel = await member.guild.create_text_channel('chatlogs', overwrites=overwrites)
        await asyncio.sleep(1)
    
    log = '```' + member.name + ' has just left the server.```'

    await logchannel.send(log)


def initialize(guild):
    conn = sqlite3.connect(settings.database(guild))
    cursor = conn.cursor()
    
    members = guild.members
    
    cursor.execute("CREATE TABLE colors(roleid INTEGER PRIMARY KEY, colorname TEXT, colorhex TEXT)")
    print('\'colors\' table created.')
    for role in guild.roles[1:]:
        color = role.color.value
        if color != 0:
            if role.permissions == role.permissions.none():
                cursor.execute("INSERT INTO colors(roleid, colorname, colorhex) VALUES (?, ?, ?)", (role.id, role.name, str(role.color)))
    print('\'colors\' table populated.')
    
    cursor.execute("ALTER TABLE users ADD color INTEGER DEFAULT '0'")
    print('\'color\' field added to \'users\' table.')
    
    for x in members:
        cursor.execute("SELECT roleid FROM colors WHERE colorhex = ?", (str(x.color),))
        colorid = cursor.fetchone()
        if colorid:
            color = colorid[0]
            cursor.execute("UPDATE users SET color = ? WHERE id = ?", (color, x.id))
            
    print('\'users\' color information populated.')
    
    conn.commit()
    conn.close()
    
command_ref = {
    "trigger": {
        "success": '```Trigger has been changed to %s```',
        "help": '```Used to change the character used before bot commands.```'
    }
}