import asyncio
import discord
import sqlite3
import datetime
import calendar
import pytz
import math
import random

import settings
import game
client = settings.client

cooldown = datetime.timedelta(seconds=10)

async def commands(message):
    command = message.content.split(" ")
    command[0] = command[0][1:]
    
    if command[0].lower() == 'bite':
        if len(command) > 1:
            if command[1].lower() == 'help':
                reply = 'Bit bite oot ouch owie.\n\nAvailable parameters: help'
                
            else:
                survivor = discord.utils.get(message.guild.roles, name='survivor')
                undead = discord.utils.get(message.guild.roles, name='undead')
                if undead in message.author.roles:
                    victim = message.mentions
                    if len(victim) > 0:
                        if survivor in victim[0].roles:
                            reply = await bite_user(message)
                            
                        else:
                            reply = 'Bite somebody living.'
                    else:
                        reply = 'Nobody mentioned'
                else:
                    reply = 'Stop biting people! You\'re not even undead!'

        await message.channel.send(reply)
        
    if command[0].lower() == 'weapon':
        if len(command) > 1:
            if command[1].lower() == 'create':
                if message.author.permissions_in(message.channel).administrator:
                    if '"' in command[2]:
                        itemstring = ''
                    
                        for param in command:
                            itemstring += ' ' + str(param)
                            
                        command[2] = itemstring.split('"')[1]
                        command[3] = itemstring.split('"')[2][1:]
                    
                    
                    conn = sqlite3.connect(settings.database(message.guild))
                    cursor = conn.cursor()
                    cursor.execute("SELECT data FROM gamedata WHERE data LIKE ? AND type = 'weapon'", (command[2] + ';%',))
                    existingweaponcheck = cursor.fetchone()
                    if existingweaponcheck is None:
                                       
                        weapondata = command[2] + ';' + command[3]
                        cursor.execute("INSERT INTO gamedata(type, data) VALUES ('weapon', ?)", (weapondata,))
                        conn.commit()
                        reply = 'New weapon "' + command[2] + '" successfully created with a power of ' + command[3] + '.'
                        
                    else:
                        reply = 'A weapon named "' + command[2] + '" already exists.'
                        
                    conn.close()
                
                
                
            elif command[1].lower() == 'check':
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT data FROM gamedata WHERE data LIKE ? AND type = 'player'", (str(message.author.id) + ';%',))
                userdata = cursor.fetchone()
                userdata = userdata[0].split(";")
                
                if userdata[2] == '0':
                    reply = 'You currently have no weapon. Good luck!'
                
                else:
                    cursor.execute("SELECT data FROM gamedata WHERE id = %s AND type = 'weapon'" % (int(userdata[2])))
                    weapondata = cursor.fetchone()
                    weapondata = weapondata[0].split(";")
                    reply = 'Your current weapon is ' + str(weapondata[0]) + ', with a power of ' + weapondata[1] + '.'
                
                conn.close()
                
            else:
                reply = 'Unrecognized parameter!'
        
        else:
            reply = 'No parameter specified.'
        
        await message.channel.send(reply)


async def bite_user(bite):
    victim = bite.mentions[0]
    survivor = discord.utils.get(bite.guild.roles, name='survivor')
    undead = discord.utils.get(bite.guild.roles, name='undead')
    conn = sqlite3.connect(settings.database(bite.guild))
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM gamedata WHERE data LIKE ? AND type = 'player'", (str(bite.author.id) + ';%',))
    biterdata = cursor.fetchone()
    conn.close()
      
    if biterdata is None:
        reply = 'Biter not found!'
        await bite.channel.send(reply)
        return
        
    else:
        biterdata = biterdata[0].split(";")
    
    if biterdata[3] == '0':
        timeelapsed = datetime.timedelta(days=1)
    else:
        lastbite = datetime.datetime.strptime(str(biterdata[3]), '%Y-%m-%d-%H-%M-%S-%f')
        timeelapsed = datetime.datetime.today() - lastbite
    
    if timeelapsed > cooldown:
        conn = sqlite3.connect(settings.database(bite.guild))
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM gamedata WHERE data LIKE ? AND type = 'player'", (str(victim.id) + ';%',))
        userdata = cursor.fetchone()[0].split(";")
        conn.close()
        
        refill(victim, bite.channel)
        
        
        if victim.nick is not None:
            vname = str(victim.nick)
        else:
            vname = str(victim.name)
        
        if biterdata[0] != '0':
            if str(bite.author.id) == '366859372879413249':
                bname = 'the stranger'
            elif bite.author.nick is not None:
                bname = str(bite.author.nick)
            else:
                bname = str(bite.author.name)
        else:
            bname = 'unknown'
            
        
        if int(userdata[1]) > 0:
            userdata[1] = str(int(userdata[1]) - 1)
            conn = sqlite3.connect(settings.database(bite.guild))
            cursor = conn.cursor()
            for field in userdata[1:]:
                userdata[0] += ';' + str(field)
            
            conn = sqlite3.connect(settings.database(bite.guild))
            cursor = conn.cursor()
            cursor.execute("UPDATE gamedata SET data = ? WHERE data LIKE ?", (str(userdata[0]), str(victim.id) + ';%'))
            conn.commit()
            conn.close()
            
            reply = bname + ' tried to attack ' + vname + ', but ' + vname + ' defended. They have ' + str(userdata[1]) + ' shots left.'
            
            await bite.channel.send(reply)
            
        else:
            
            reply = '```' + bname + ' bit ' + vname + '! Treat your wounds or you will die!```'
            
            sent = await bite.channel.send(reply)
            
            emoji = '\U0001F489'
            await sent.add_reaction(emoji)
            
            conn = sqlite3.connect(settings.database(bite.guild))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO commanddata(user, message, type, data) VALUES (?, ?, ?, ?)", (victim.id, sent.id, 'death', '0'))
            conn.commit()
            conn.close()
            
            client.loop.create_task(last_stand(sent, bite.channel))
        
        biterdata[3] = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S-%f')
        
        for field in biterdata[1:]:
            biterdata[0] += ';' + str(field)
        
        conn = sqlite3.connect(settings.database(bite.guild))
        cursor = conn.cursor()
        cursor.execute("UPDATE gamedata SET data = ? WHERE data LIKE ?", (str(biterdata[0]), str(bite.author.id) + ';%'))
        conn.commit()
        conn.close()
    else:
        secleft = (cooldown - timeelapsed)
        minleft = secleft.seconds / 60
        
        if int(minleft) >= 1:
            reply = 'You are not hungry again yet, ' + bname + '. Cooldown ends in ' + str(int(minleft)) + ' minutes.'
        else:
            reply = 'You are not hungry again yet, ' + bname + '. Cooldown ends in less than one minute.'
        
        await bite.channel.send(reply)


def drop_item(user, strength, guild):
    conn = sqlite3.connect(settings.database(guild))
    cursor = conn.cursor()
    cursor.execute("SELECT id, data FROM gamedata WHERE type = 'weapon' AND data LIKE ?", ('%;' + str(strength),))
    lvlweapons = cursor.fetchall()
    
    newweapon = [[], [], []]
    
    if lvlweapons is None:
        reply = 'It was empty.'
        conn.close()
        return reply

    else:
        random.shuffle(lvlweapons)
        newweapon[0] = lvlweapons[0][0]
        newweapon[1] = lvlweapons[0][1].split(";")[0]
        newweapon[2] = lvlweapons[0][1].split(";")[1]
    
    cursor.execute("SELECT data FROM gamedata WHERE type = 'player' AND data LIKE ?", (str(user.id) + ';%',))
    userdata = cursor.fetchone()
    userdata = userdata[0].split(";")
    
    if str(userdata[2]) != str(newweapon[0]):
        userdata[2] = newweapon[0]
    
        for field in userdata[1:]:
            userdata[0] += ';' + str(field)
            
        cursor.execute("UPDATE gamedata SET data = ? WHERE data LIKE ?", (userdata[0], str(user.id) + ';%'))
        
        conn.commit()
        
        
        if str(user.nick) != 'None':
            reply = '```' + str(user.nick) + ' got ' + str(newweapon[1]) + ' (clip size ' + str(newweapon[2]) + ')```'
        else:
            reply = '```' + str(user.name) + ' got ' + str(newweapon[1]) + ' (clip size ' + str(newweapon[2]) + ')```'
    else:
        if str(user.nick) != 'None':
            reply = '```' + str(user.nick) + ' got ' + str(newweapon[1]) + '...? They\'ve already got that...```'
        else:
            reply = '```' + str(user.name) + ' got ' + str(newweapon[1]) + '...? They\'ve already got that...```'
    
    conn.close()
    return reply


async def random_biter(channel):
    
    undead = discord.utils.get(channel.guild.roles, name='undead')
    
    thisbot = discord.utils.get(channel.guild.members, id=client.user.id)
    await thisbot.add_roles(undead, atomic=True)
    
    minmax = 3
    minmin = 1
    period = random.randint(minmin * 5, minmax * 5)
    await asyncio.sleep(cooldown.seconds + period)
    
    
    while game.gamestatus(1, channel.guild) == 1:
        survivor = discord.utils.get(channel.guild.roles, name='survivor')
        
        survivors = survivor.members
                
        random.shuffle(survivors)
        await bite_user(thisbot, survivors[0], channel)
        period = random.randint(minmin * 5, minmax * 5)
        await asyncio.sleep(cooldown.seconds + period)
        
    await thisbot.remove_roles(undead, atomic=True)
    
    
# async def auto_refill(channel):
    
    # await asyncio.sleep(3)
    
    # while gamestatus(1) == 1:
        
        # survivor = discord.utils.get(channel.guild.roles, name='survivor')
        
        # survivors = survivor.members
        # for player in survivors:
            # refill(player)
                
        # await asyncio.sleep(3)
    
    
async def item_spawn(channel):
    
    minmax = 4
    minmin = 2
    
    period = random.randint(minmin * 5, minmax * 5)
    await asyncio.sleep(period)
    
    while game.gamestatus(1, channel.guild) == 1:
    
        undeadcount = 0
        
        for player in channel.guild.members:
            undead = discord.utils.get(channel.guild.roles, name='undead')
            userroles = player.roles
                
            if undead in userroles:
                undeadcount += 1
                
        
        strength = int((undeadcount / 3) * 2)
        
        if strength > 0:
            sent = await channel.send('An item has dropped!')
            emoji = '\U0001F4E6'
            await sent.add_reaction(emoji)
            
            conn = sqlite3.connect(settings.database(channel.guild))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO commanddata(user, message, type, data) VALUES (?, ?, ?, ?)", (0, sent.id, 'lootdrop', strength))
            conn.commit()
            conn.close()
        
        
        period = random.randint(minmin * 5, minmax * 5)
        await asyncio.sleep(period)
    

async def last_stand(command, channel):

    await asyncio.sleep(10)
    
    conn = sqlite3.connect(settings.database(channel.guild))
    cursor = conn.cursor()
    cursor.execute("SELECT user, data FROM commanddata WHERE message = ? AND type = 'death'", (command.id,))
    results = cursor.fetchone()
    conn.close()
    
    if results[1] == '0' and game.gamestatus(1, channel.guild) == 1:
        survivor = discord.utils.get(channel.guild.roles, name='survivor')
        undead = discord.utils.get(channel.guild.roles, name='undead')
        deadperson = discord.utils.get(channel.guild.members, id=int(results[0]))
        
        if deadperson.nick is not None:
            dname = str(deadperson.nick)
        else:
            dname = str(deadperson.name)
    
        reply = '```' + dname + ' has died!```'
        
        print('Passed this one')
        
        await command.edit(content=reply)
        await command.remove_reaction('\U0001F489', client.user)
        
        #sent = await channel.send(reply)
        
        await deadperson.add_roles(undead, atomic=True)
            
        await deadperson.remove_roles(survivor, atomic=True)
            
        await asyncio.sleep(2)        
        survivors = survivor.members
        
        if len(survivors) < 2:
            if survivors[0].nick is not None:
                wname = str(survivors[0].nick)
            else:
                wname = str(survivors[0].name)
            
            reply = '```Game over! ' + wname + ' wins!```'
            await channel.send(reply)
            
            await game.end_game(1, channel.guild)
    
    else:
        conn = sqlite3.connect(settings.database(channel.guild))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM commanddata WHERE message = ? AND type = 'death'", (command,))
        conn.commit()
        conn.close()
        

def refill(user, channel):
    conn = sqlite3.connect(settings.database(channel.guild))
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM gamedata WHERE data LIKE ? AND type = 'player'", (str(user.id) + ';%',))
    userdata = cursor.fetchone()[0].split(";")
    if userdata[2] != '0':
        cursor.execute("SELECT data FROM gamedata WHERE id = ? AND type = 'weapon'", (userdata[2],))
        weapondata = cursor.fetchone()[0].split(";")
    else:
        weapondata = [[], [], []]
        weapondata[0] = '0'
        weapondata[1] = '0'
    conn.close()
    
    if weapondata[1] != '0':
        if userdata[3] == '0':
            userdata[3] = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S-%f')
        else:
            lastrefill = datetime.datetime.strptime(str(userdata[3]), '%Y-%m-%d-%H-%M-%S-%f')
            timesince = datetime.datetime.today() - lastrefill
            refills = int(timesince.seconds / cooldown.seconds) * int(weapondata[1])
            userdata[1] = str(int(userdata[1]) + refills)
            lastrefill = lastrefill + ((cooldown/int(weapondata[1])) * refills)
            userdata[3] = lastrefill.strftime('%Y-%m-%d-%H-%M-%S-%f')
            if int(userdata[1]) > int(weapondata[1]):
                userdata[1] = weapondata[1]

        for field in userdata[1:]:
            userdata[0] += ';' + str(field)
        
        conn = sqlite3.connect(settings.database(channel.guild))
        cursor = conn.cursor()    
        cursor.execute("UPDATE gamedata SET data = ? WHERE data LIKE ?", (str(userdata[0]), str(user.id) + ';%'))
        conn.commit()
        conn.close()


async def start(message):
    conn = sqlite3.connect(settings.database(message.guild))
    cursor = conn.cursor()

    cursor.execute("DELETE FROM gamedata WHERE type = 'player'")
    thisbot = discord.utils.get(message.guild.members, id=client.user.id)
    readyrole = discord.utils.get(message.guild.roles, name='survivor')
    await thisbot.add_roles(readyrole, atomic=True)
    await asyncio.sleep(1)
    
    cursor.execute("SELECT id FROM gamedata WHERE type = 'weapon' AND data LIKE ?", ('%;0',))
    nullweap = cursor.fetchone()[0]
                                
    for player in message.guild.members:
        
        userroles = player.roles
            
        if readyrole in userroles:
            playerdata = str(player.id) + ';0;' + str(nullweap) + ';0'                                    
            
            cursor.execute("INSERT INTO gamedata(type, data) VALUES ('player', ?)", (playerdata,))
            
    cursor.execute("SELECT data FROM gamedata WHERE type = 'gamemode' AND data LIKE ?", ('1;%',))
    gamedata = cursor.fetchone()
    gamedata = gamedata[0].split(";")
    gamedata[2] = '1'
    
    for item in gamedata[1:]:
        gamedata[0] += ';' + str(item)
    
    cursor.execute("UPDATE gamedata SET data = ? WHERE type = 'gamemode' AND data LIKE ?", (str(gamedata[0]), '1;%'))
            
    conn.commit()
    conn.close()
    await thisbot.remove_roles(readyrole, atomic=True)

    client.loop.create_task(random_biter(message.channel))
    client.loop.create_task(item_spawn(message.channel))
    

    reply = 'Starting game...'
    
    return reply