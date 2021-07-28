import asyncio
import discord
import sqlite3
import datetime
import calendar
import pytz
import math
import random
import json

import settings
import utilities

client = settings.client

initdate = datetime.date(2019, 5, 20)

async def commands(message):
    command = message.content.split(" ")
    command[0] = command[0][1:]
    
    if command[0].lower() == 'cheer':
        if len(command) > 1:
            if command[1].lower() == 'set':
                if len(command) > 2:
                    try:
                        conn = sqlite3.connect(settings.database(message.guild))
                        cursor = conn.cursor()
                        cursor.execute("UPDATE config SET value = ? WHERE key = 'cheer'", (command[2],))
                        conn.commit()
                        conn.close()
                        await message.channel.send('```The cheer emote has been successfully set to ' + command[2] + '```')
                    except:
                        await message.channel.send('```Something went wrong.```')
            
                else:
                    await message.channel.send('```Follow that command with an emote to set it as the cheer for this server.```')
                    
            else:
                await message.channel.send('```Unknown parameter ' + command[1] + '```')
        else:
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = 'cheer'")
            cheeremote = cursor.fetchone()
            conn.close()
            await message.channel.send('```The cheer emote is currently set to ' + cheeremote[0] + '```')
    
    if command[0].lower() == 'timezone':
        if len(command) > 1:
            if command[1].lower() == 'help':
                await message.channel.send('```Allows you to check or set your time zone for study logs. Use by itself to check your current setting, or with a timezone name to change your timezone.\n\nAvailable parameters: help```')
            
            else:
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT tzname, id FROM timezones WHERE tzname LIKE ?", ('%' + command[1] + '%',))
                tzsearchresults = cursor.fetchall()
                
                
                if len(tzsearchresults) > 0:
                    if len(tzsearchresults) == 1:
                        cursor.execute("UPDATE users SET timezone = ? WHERE id = ?", (tzsearchresults[0][1], message.author.id))
                        conn.commit()
                        await message.channel.send('```Your timezone has been successfully set to %s.```' % (tzsearchresults[0][0]))
                    
                    else:
                        resultsreply = '```Timezones containing "' + command[1] + '":\n\n'

                        for result in tzsearchresults:
                            resultsreply = resultsreply + '        ' + result[0] + '\n'
                        
                        resultsreply += '```'
                        
                        await message.channel.send(resultsreply)
                        
                else:
                    await message.channel.send('```No timezone containing "%s" found.```' % (command[1]))
                
                conn.close()

        else:
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (message.author.id,))
            usertz = cursor.fetchone()
            conn.close()
            await message.channel.send('```Your current timezone is set to %s.```' % (usertz[0]))
            
    if command[0].lower() == 'mark':
        datetext = ''
        userfound = False
        validcheck = False
        
        if len(command) > 1:
            if command[1].lower() == 'help':
                replymessage = '```Logs you as having studied for a given date. By itself it logs for the current date, but a date can be specified using a day (DD) in the current month, a month and day in this year (MM-DD) or a full date format (YYYY-MM-DD).\n\nAvailable parameters: help```'
            
            
            elif command[1].lower() == 'for' and message.author.permissions_in(message.channel).administrator:
                usersearch = await utilities.findmember(message.guild, command[2])
                
                if len(usersearch) > 1:
                    if len(usersearch) > 10:
                        replymessage = '```More than 10 users found.```'
                        
                    else:
                        userstreakreply = '```More than one user found.\n'
                        
                        for person in usersearch:
                            founduser = message.guild.get_member(person[0])
                            if founduser.nick is None:
                                userstreakreply = userstreakreply + '\n\t' + founduser.name
                            else:
                                userstreakreply = userstreakreply + '\n\t' + founduser.nick
                            
                        replymessage = userstreakreply + '```'
                            
                elif len(usersearch) == 0:
                    replymessage = '```No users found.```'
                    
                else:
                    inputuser = message.guild.get_member(usersearch[0][0])
                    userfound = True
                    
                    if len(command) > 3:
                        datetext = command[3]
            
            else:
                inputuser = message.author
                userfound = True
                datetext = command[1]
                
        else:
            inputuser = message.author
            userfound = True

        if userfound:
        
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (inputuser.id,))
            usertz = cursor.fetchone()
            conn.close()
            today = datetime.datetime.now(pytz.timezone(usertz[0])).date()
            
            if inputuser.nick is None:
                username = inputuser.name
            else:
                username = inputuser.nick
            
            if len(datetext) > 0:
                results = await utilities.checkdate(datetext, today)
                if isinstance(results, datetime.date):
                    validcheck = True
                    inputdate = results
                else:
                    if results == 0:
                        replymessage = '```Invalid parameter.```'
                    elif results == 1:
                        replymessage = '```Invalid day.```'
                    elif results == 2:
                        replymessage = '```Invalid month.```'
                    elif results == 3:
                        replymessage = '```Invalid day and month.```'
                    elif results == 4:
                        replymessage = '```Invalid year. Only values from the past 100 years and the next 100 years are accepted.```'
                    elif results == 5:
                        replymessage = '```Invalid year and day.```'
                    elif results == 6:
                        replymessage = '```Invalid year and month.```'
                    elif results == 7:
                        replymessage = '```Invalid year, month and day. Everything\'s wrong. Terrible.```'
                    elif results == 8:
                        replymessage = '```??? SOMETHING WENT WRONG ???```'
            
            else:
                inputdate = today
                validcheck = True


        if validcheck:
            if inputdate >= initdate:
                if inputdate <= today:
                    conn = sqlite3.connect(settings.database(message.guild))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, inputdate))
                    check = cursor.fetchone()

                    if check[0] > 0:
                        if inputuser == message.author:
                            replymessage = '```You have already been marked for that day.```'
                        else:
                            replymessage = '```' + username + ' has already been marked for that day.```'

                    else:
                        cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, inputdate - datetime.timedelta(days=1)))
                        streak = cursor.fetchone()
                        if streak:
                            cursor.execute("INSERT INTO studysessions(userid, datestudied, streak) VALUES (?, ?, ?)", (inputuser.id, inputdate, streak[0] + 1))
                        else:
                            cursor.execute("INSERT INTO studysessions(userid, datestudied, streak) VALUES (?, ?, ?)", (inputuser.id, inputdate, 1))

                        conn.commit()

                        cursor.execute("SELECT datestudied FROM studysessions WHERE userid = ? AND datestudied >= ? ORDER BY datestudied ASC", (inputuser.id, inputdate))
                        entries = cursor.fetchall()

                        i = 0
                        cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, inputdate))
                        iterstreak = cursor.fetchone()

                        entry = entries[0][0].split("-")
                        entrydate = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))

                        while entrydate == (inputdate + datetime.timedelta(days=i)):

                            cursor.execute("UPDATE studysessions SET streak = ? WHERE userid = ? AND datestudied = ?", (iterstreak[0] + i, inputuser.id, entrydate))

                            i += 1
                            if i < (len(entries)):
                                entry = entries[i][0].split("-")
                                entrydate = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))

                        replymessage = '```Study has been successfully logged for ' + inputdate.strftime('%Y-%m-%d') + '.```'
                        
                        # try:
                        cheer = settings.cheer(message.guild)
                        
                        if cheer:
                            clapping = discord.utils.get(message.guild.emojis, name=cheer)
                            
                            #if not clapping:
                                #clapping = '\U0001F44D'
                        else:
                            clapping = '\U0001F44D'
                        
                        try:
                            await message.add_reaction(clapping)
                        except:
                            await message.add_reaction('\U0001F44D')
                            
                    conn.commit()
                    conn.close()
                    
                else:
                    replymessage = '```It is too early to report for that day.```'
                
            else:
                replymessage = '```Logs can only be entered as far back as May 20th, 2019.```'
        
        
        await message.channel.send(replymessage)
    

    if command[0].lower() == 'unmark':
        datetext = ''
        validcheck = False
        userfound = False
        
        if len(command) > 1:
            if command[1].lower() == 'help':
                replymessage = '```Unlogs you as having studied for a given date. By itself it unlogs for the current date, but a date can be specified using a day (DD) in the current month, a month and day in this year (MM-DD) or a full date format (YYYY-MM-DD).\n\nAvailable parameters: help```'
            
            elif command[1].lower() == 'for' and message.author.permissions_in(message.channel).administrator:
                usersearch = utilities.findmember(message.guild, command[2])
                    
                if len(usersearch) > 1:
                    if len(usersearch) > 10:
                        replymessage = '```More than 10 users found.```'
                        
                    else:
                        userstreakreply = '```More than one user found.\n'
                        
                        for person in usersearch:
                            founduser = message.guild.get_member(person[0])
                            if founduser.nick is None:
                                userstreakreply = userstreakreply + '\n\t' + founduser.name
                            else:
                                userstreakreply = userstreakreply + '\n\t' + founduser.nick
                            
                        replymessage = userstreakreply + '```'
                            
                elif len(usersearch) == 0:
                    replymessage = '```No users found.```'
                    
                else:
                    inputuser = message.guild.get_member(usersearch[0][0])
                    userfound = True
                    
                    if len(command) > 3:
                        datetext = command[3]
            
            else:
                inputuser = message.author
                userfound = True
                datetext = command[1]
                
        else:
            inputuser = message.author
            userfound = True

        if userfound:
        
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (inputuser.id,))
            usertz = cursor.fetchone()
            conn.close()
            today = datetime.datetime.now(pytz.timezone(usertz[0])).date()
            
            if inputuser.nick is None:
                username = inputuser.name
            else:
                username = inputuser.nick
            
            if len(datetext) > 0:
                results = await utilities.checkdate(datetext, today)
                if isinstance(results, datetime.date):
                    validcheck = True
                    inputdate = results
                else:
                    if results == 0:
                        replymessage = '```Invalid parameter.```'
                    elif results == 1:
                        replymessage = '```Invalid day.```'
                    elif results == 2:
                        replymessage = '```Invalid month.```'
                    elif results == 3:
                        replymessage = '```Invalid day and month.```'
                    elif results == 4:
                        replymessage = '```Invalid year. Only values from the past 100 years and the next 100 years are accepted.```'
                    elif results == 5:
                        replymessage = '```Invalid year and day.```'
                    elif results == 6:
                        replymessage = '```Invalid year and month.```'
                    elif results == 7:
                        replymessage = '```Invalid year, month and day. Everything\'s wrong. Terrible.```'
                    elif results == 8:
                        replymessage = '```??? SOMETHING WENT WRONG ???```'
            
            else:
                inputdate = today
                validcheck = True
            
        if validcheck:
            
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, inputdate))
            check = cursor.fetchone()

            if check[0] > 0:
                cursor.execute("DELETE FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, inputdate))
                conn.commit()
                
                cursor.execute("SELECT datestudied FROM studysessions WHERE userid = ? AND datestudied > ? ORDER BY datestudied ASC", (inputuser.id, inputdate))
                entries = cursor.fetchall()
                
                if len(entries) > 0:
                    i = 1
                    
                    entrydate = datetime.datetime.strptime(entries[0][0], '%Y-%m-%d').date()
                    
                    while entrydate == (inputdate + datetime.timedelta(days=i)):
                        print(str(entrydate))
                        print(str(inputdate + datetime.timedelta(days=i)))
                        
                        cursor.execute("UPDATE studysessions SET streak = ? WHERE userid = ? AND datestudied = ?", (i, inputuser.id, entrydate))
                        conn.commit()
                        
                        if i < (len(entries)):
                            entrydate = datetime.datetime.strptime(entries[i][0], '%Y-%m-%d').date()
                            
                        i += 1
                        print(i)
                            
                replymessage = '```Study log successfully removed.```'

            else:
                if inputuser == message.author:
                    replymessage = '```You have no log for that day.```'
                else:
                    replymessage = '```' + username + ' has no log for that day.```'
                
            conn.close()
        
        await message.channel.send(replymessage)
        
            
    
    if command[0].lower() == 'didistudy':
        conn = sqlite3.connect(settings.database(message.guild))
        cursor = conn.cursor()
        cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (message.author.id,))
        usertz = cursor.fetchone()
        conn.close()
        today = datetime.datetime.now(pytz.timezone(usertz[0])).date()
        validcheck = False

        if len(command) > 1:
            if command[1].lower() == 'help':
                replymessage = '```Checks if study has been logged for the date given. By itself it checks for the current date, but a date can be specified using a day in the current month or using the YYYY-MM-DD format.\n\nAvailable parameters: help```'
            
            else:
                results = await utilities.checkdate(command[1], today)
                if isinstance(results, datetime.date):
                    validcheck = True
                    inputdate = results
                else:
                    if results == 0:
                        replymessage = '```Invalid parameter.```'
                    elif results == 1:
                        replymessage = '```Invalid day.```'
                    elif results == 2:
                        replymessage = '```Invalid month.```'
                    elif results == 3:
                        replymessage = '```Invalid day and month.```'
                    elif results == 4:
                        replymessage = '```Invalid year. Only values from the past 100 years and the next 100 years are accepted.```'
                    elif results == 5:
                        replymessage = '```Invalid year and day.```'
                    elif results == 6:
                        replymessage = '```Invalid year and month.```'
                    elif results == 7:
                        replymessage = '```Invalid year, month and day. Everything\'s wrong. Terrible.```'
                    elif results == 8:
                        replymessage = '```??? SOMETHING WENT WRONG ???```'
            
        else:
            inputdate = today
            validcheck = True

        if validcheck:
            if inputdate >= initdate:
                if inputdate <= today:
                    conn = sqlite3.connect(settings.database(message.guild))
                    cursor = conn.cursor()

                    cursor.execute("SELECT COUNT(*) FROM studysessions WHERE userid = ? AND datestudied = ?", (message.author.id, inputdate))
                    check = cursor.fetchone()

                    if check[0] > 0:
                        replymessage = '```Yes, you studied on ' + inputdate.strftime('%Y-%m-%d') + '.```'

                    else:
                        replymessage = '```You have no study logged for ' + inputdate.strftime('%Y-%m-%d') + '.```'

                    conn.close()

                else:
                    replymessage = '```There are no logs for dates in the future.```'
            else:
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT datestudied FROM studysessions WHERE userid = ? ORDER BY datestudied ASC", (message.author.id,))
                first = cursor.fetchone()
                
                if first:
                    replymessage = '```Logs only go as far back as May 20th, 2019. Your first recorded study was on ' + first[0] + '.```'
                else:
                    replymessage = '```You have yet to report any study sessions!```'
                
        await message.channel.send(replymessage)
    
    if command[0].lower() == 'streak':
        if len(command) > 1:
            if command[1].lower() == 'help':
                await message.channel.send('```Returns study streak statistics. Statistics for other users can be looked up using the "user" parameter.\n\nAvailable parameters: help, longest, current, user```')
                
            elif command[1].lower() == 'longest':
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(streak) FROM studysessions WHERE userid = ?", (message.author.id,))
                maxstreak = cursor.fetchone()
                conn.close()
                
                if maxstreak[0]:
                    await message.channel.send('```Your longest streak is ' + str(maxstreak[0]) + ' days.```')
                else:
                    await message.channel.send('```You have yet to report any study sessions!```')
            
            elif command[1].lower() == 'current':
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (message.author.id,))
                usertz = cursor.fetchone()
                today = datetime.datetime.now(pytz.timezone(usertz[0])).date()
                cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (message.author.id, today))
                nowstreak = cursor.fetchone()
                if not nowstreak:
                    cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (message.author.id, today - datetime.timedelta(days=1)))
                    nowstreak = cursor.fetchone()
                    
                if nowstreak:
                    await message.channel.send('```Your current streak is ' + str(nowstreak[0]) + ' days.```')
                else:
                    await message.channel.send('```You are currently not in a streak.```')
              
            elif command[1].lower() == 'user':
                if len(command) > 2:
                    conn = sqlite3.connect(settings.database(message.guild))
                    cursor = conn.cursor()
                    cursor.execute("SELECT users.id, users.nickname, timezones.tzname, users.username FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.username LIKE ? OR users.nickname LIKE ?", ('%' + command[2] + '%', '%' + command[2] + '%'))
                    usersearch = cursor.fetchall()
                    userstreakreply = '```' + str(len(usersearch)) + ' user(s) found.'
                    
                    for person in usersearch:
                        founduser = message.guild.get_member(person[0])
                        userstreakreply = userstreakreply + '\n\n'
                        today = datetime.datetime.now(pytz.timezone(person[2])).date()
                        if founduser.nick is None:
                            userstreakreply = userstreakreply + '\t~~' + founduser.name + '~~\n'
                        else:
                            userstreakreply = userstreakreply + '\t~~' + founduser.nick + '~~\n'
                            
                        cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (person[0], today))
                        usernow = cursor.fetchone()
                        if not usernow:
                            cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (person[0], today - datetime.timedelta(days=1)))
                            usernow = cursor.fetchone()
                            
                        cursor.execute("SELECT MAX(streak) FROM studysessions WHERE userid = ?", (person[0],))
                        usermax = cursor.fetchone()
                        if usermax[0]:
                            userstreakreply = userstreakreply + '\tLongest streak-\t' + str(usermax[0]) + ' days\n'
                            if usernow:
                                userstreakreply = userstreakreply + '\tCurrent streak-\t' + str(usernow[0]) + ' days'
                            else:
                                userstreakreply = userstreakreply + '\tCurrent streak-\tNone'
                        else:
                            userstreakreply = userstreakreply + '\tNo study data found!'
                        
                    userstreakreply = userstreakreply + '```'
                        
                    await message.channel.send(userstreakreply)                    
                    conn.close()
                    
                else:
                    await message.channel.send('```Please specify a user to look up in your search.```')
            
            else:
                await message.channel.send('```Unrecognized parameter. Available parameters:\n  help, longest, current```')
            
        else:
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (message.author.id,))
            usertz = cursor.fetchone()
            today = datetime.datetime.now(pytz.timezone(usertz[0])).date()
            cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (message.author.id, today))
            nowstreak = cursor.fetchone()
            if not nowstreak:
                cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (message.author.id, today - datetime.timedelta(days=1)))
                nowstreak = cursor.fetchone()
                
            cursor.execute("SELECT MAX(streak) FROM studysessions WHERE userid = ?", (message.author.id,))
            maxstreak = cursor.fetchone()
            conn.close()
            streakreply = '```Streak statistics for ' + message.author.name + ':\n'
            if maxstreak[0]:
                streakreply = streakreply + '\tLongest streak-\t' + str(maxstreak[0]) + ' days\n'
                if nowstreak:
                    streakreply = streakreply + '\tCurrent streak-\t' + str(nowstreak[0]) + ' days'
                else:
                    streakreply = streakreply + '\tCurrent streak-\tNone'
            else:
                streakreply = streakreply + '\tNo study data found!'
                
            streakreply = streakreply + '```'
            
            await message.channel.send(streakreply)
            
            
    if command[0].lower() == 'leaderboard':
        if len(command) > 1:
            if command[1].lower() == 'help':
                await message.channel.send('```Displays a leaderboard of the top studyers on the server. Categories available are alltime longest streak, current longest streak, and days studied total.\n\nAvailable parameters: help, alltime, current, days```')
            
            elif command[1].lower() == 'alltime':
                alltimelist = [[], []]
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT users.id, MAX(studysessions.streak), users.active FROM users JOIN studysessions ON studysessions.userid = users.id GROUP BY users.id")
                tops = cursor.fetchall()
                conn.close()
                
                tops.sort(reverse=True, key=lambda x: x[1])
                
                topresults = '```Top study streaks of all time:\n'
                
                for row in tops:
                    if row[2] == 1:
                        founduser = message.guild.get_member(row[0])
                        if founduser.nick is None:
                            topresults = topresults + '\n\t' + '{:32}'.format(founduser.name + ':') + '\t' + str(row[1]) + ' days'
                        else:
                            topresults = topresults + '\n\t' + '{:32}'.format(founduser.nick + ':') + '\t' + str(row[1]) + ' days'
                
                topresults = topresults + '```'
                
                await message.channel.send(topresults)
                
            elif command[1].lower() == 'current':
            
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT users.id, timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id")
                allusers = cursor.fetchall()
                
                recenttop = []
                for entry in allusers:
                    cursor.execute("SELECT users.id, studysessions.streak, users.active FROM users JOIN studysessions ON studysessions.userid = users.id WHERE users.id = ? AND studysessions.datestudied = ? ORDER BY studysessions.datestudied ASC", (entry[0], datetime.datetime.now(pytz.timezone(entry[1])).date()))
                    mostrecent = cursor.fetchone()
                    
                    if mostrecent:
                        recenttop.append(mostrecent)
                        
                    else:
                        cursor.execute("SELECT users.id, studysessions.streak, users.active FROM users JOIN studysessions ON studysessions.userid = users.id WHERE users.id = ? AND studysessions.datestudied = ? ORDER BY studysessions.datestudied ASC", (entry[0], datetime.datetime.now(pytz.timezone(entry[1])).date() - datetime.timedelta(days=1)))
                        mostrecent = cursor.fetchone()
                        if mostrecent:
                            recenttop.append(mostrecent)

                                
                recenttop.sort(reverse=True, key=lambda x: x[1])
                
                curresults = '```Top study streaks right now:\n'
                
                for row in recenttop:
                    if row[2] == 1:
                        founduser = message.guild.get_member(row[0])
                        if founduser.nick is None:
                            curresults = curresults + '\n\t' + '{:32}'.format(founduser.name) + ':\t' + str(row[1]) + ' days'
                        else:
                            curresults = curresults + '\n\t' + '{:32}'.format(founduser.nick) + ':\t' + str(row[1]) + ' days'
                
                curresults = curresults + '```'
                
                conn.close()
                await message.channel.send(curresults)
                
                
            elif command[1].lower() == 'days':
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT users.id, COUNT(studysessions.datestudied), users.active FROM users JOIN studysessions ON studysessions.userid = users.id GROUP BY users.id")
                totdays = cursor.fetchall()
                
                totdays.sort(reverse=True, key=lambda x: x[1])
                
                daysresults = '```Most days studied total:\n'
                
                for row in totdays:
                    if row[2] == 1:
                        founduser = message.guild.get_member(row[0])
                        if founduser.nick is None:
                            daysresults = daysresults + '\n\t' + '{:32}'.format(founduser.name) + ':\t' + str(row[1]) + ' days'
                        else:
                            daysresults = daysresults + '\n\t' + '{:32}'.format(founduser.nick) + ':\t' + str(row[1]) + ' days'
                        
                daysresults = daysresults + '```'
                
                conn.close()
                await message.channel.send(daysresults)
                
                            
            else:
                await message.channel.send('```Unrecognized parameter. Available parameters:\n  help, alltime, current, days```')
        else:
            await message.channel.send('```Please specify which type of statistics you would like to see.\n  Options: alltime, current, days```')
            
            
    if command[0].lower() == 'calendar':
        conn = sqlite3.connect(settings.database(message.guild))
        cursor = conn.cursor()
        cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (message.author.id,))
        usertz = cursor.fetchone()
        conn.close()
        today = datetime.datetime.now(pytz.timezone(usertz[0])).date()
        validdate = False
        
        if len(command) > 1:
            if command[1].lower() == 'help':
                reply = '```Shows study logs graphically on a calendar. By itself it will show the current month, but a month can be specified using a month in the current year or using the YYYY-MM format. \n\nAvailable parameters: help```'
            
            else:
                inputdate = await utilities.checkdate(command[1], today)
                
                if isinstance(inputdate, datetime.date):
                    validdate = True
                    
                else:
                    if inputdate == 0:
                        reply = '```Invalid parameter.```'
                    elif inputdate == 1:
                        reply = '```Invalid day.```'
                    elif inputdate == 2:
                        reply = '```Invalid month.```'
                    elif inputdate == 3:
                        reply = '```Invalid day and month.```'
                    elif inputdate == 4:
                        reply = '```Invalid year. Only values from the past 100 years and the next 100 years are accepted.```'
                    elif inputdate == 5:
                        reply = '```Invalid year and day.```'
                    elif inputdate == 6:
                        reply = '```Invalid year and month.```'
                    elif inputdate == 7:
                        reply = '```Invalid year, month and day. Everything\'s wrong. Terrible.```'
                    elif inputdate == 8:
                        reply = '```??? SOMETHING WENT WRONG ???```'
            
        else:
            inputdate = today
            inputdate.replace(day=1)
            validdate = True
            
        if validdate: 
        
            newcalendar = drawcalendar(message.author, message, inputdate)
        
            sent = await message.channel.send(newcalendar)
                
            emoji = '\u2B05'
            await sent.add_reaction(emoji)
            emoji = '\u27A1'
            await sent.add_reaction(emoji)
            
            conn = sqlite3.connect(settings.database(message.guild))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO commanddata(message, type, user, data) VALUES (?, ?, ?, ?)", (sent.id, 'calendar', message.author.id, inputdate.strftime('%Y-%m-%d')))
            conn.commit()
            conn.close()
        
        else:
            await message.channel.send(reply)

    if command[0].lower() == 'backup':
        if message.author.permissions_in(message.channel).administrator:
            today = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            reply = ''
            
            try:
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                cursor.execute("SELECT userid, datestudied, streak FROM studysessions")
                alllogs = cursor.fetchall()
                conn.close()
                
                if alllogs:
                
                    backupdict = {'logs': []}
                
                    for row in alllogs:
                        backupdict['logs'].append([row[0], row[1], row[2]])
                    
                    with open(settings.backup(message.guild) + '_BACKUP_' + today + '.json', 'w') as backupf:
                        json.dump(backupdict, backupf)
                
                    reply = str(len(alllogs)) + ' study logs backed up successfully.'
                
                else:
                    reply = 'No logs found.'
                    
            except:
                reply = 'Backup failed.'
                
            await message.channel.send(reply)
            
    if command[0].lower() == 'import':
        if message.author.permissions_in(message.channel).administrator:
            reply = ''
                
            try:
                with open(settings.backuppath + command[1] + '.json', 'r') as backupf:
                    backupdict = json.load(backupf)
                
                conn = sqlite3.connect(settings.database(message.guild))
                cursor = conn.cursor()
                
                importcount = 0
                
                for item in backupdict['logs']:
                    inputuserid = item[0]
                    inputdate = datetime.datetime.strptime(item[1], '%Y-%m-%d').date()
                    inputstreak = item[2]
                
                    cursor.execute("SELECT COUNT(*) FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuserid, inputdate))
                    check = cursor.fetchone()

                    if check[0] == 0:
                        cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuserid, inputdate - datetime.timedelta(days=1)))
                        streak = cursor.fetchone()
                        if streak:
                            cursor.execute("INSERT INTO studysessions(userid, datestudied, streak) VALUES (?, ?, ?)", (inputuserid, inputdate, streak[0] + 1))
                        else:
                            cursor.execute("INSERT INTO studysessions(userid, datestudied, streak) VALUES (?, ?, ?)", (inputuserid, inputdate, 1))

                        conn.commit()

                        cursor.execute("SELECT datestudied FROM studysessions WHERE userid = ? AND datestudied >= ? ORDER BY datestudied ASC", (inputuserid, inputdate))
                        entries = cursor.fetchall()

                        i = 0
                        cursor.execute("SELECT streak FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuserid, inputdate))
                        iterstreak = cursor.fetchone()

                        entry = entries[0][0].split("-")
                        entrydate = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))

                        while entrydate == (inputdate + datetime.timedelta(days=i)):
                            cursor.execute("UPDATE studysessions SET streak = ? WHERE userid = ? AND datestudied = ?", (iterstreak[0] + i, inputuserid, entrydate))
                            conn.commit()
                            
                            i += 1
                            if i < (len(entries)):
                                entry = entries[i][0].split("-")
                                entrydate = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))
                            
                        importcount += 1

                conn.close()
                reply = '```' + str(importcount) + ' study logs imported.```'
                
            except:
                reply = '```Import failed.```'
                
            await message.channel.send(reply)
                
                
    
    if command[0].lower() == 'kana':
        if command[1].lower() == 'add':
            if message.author.permissions_in(message.channel).administrator:
                if len(command) > 5:
                    try:
                        with open(settings.datapath + 'kana.json', 'r') as kanaf:
                            kana = json.load(kanaf)
                        
                        try:
                            kana[command[2]][command[3]].append([command[4], command[5]])
                        except:
                            try:
                                kana[command[2]][command[3]] = [[command[4], command[5]]]
                                
                            except:
                                kana[command[2]] = {command[3]: [[command[4], command[5]]]}

                    except:
                        print('That file or dictionary not found')
                        kana = {command[2]: {command[3]: [[command[4]], [command[5]]]}}
                        
                    with open(settings.datapath + 'kana.json', 'w') as kanaf:
                        
                        json.dump(kana, kanaf)
        
        elif command[1].lower() == 'print':
            with open(settings.datapath + 'kana.json', 'r') as kanaf:
                kana = json.load(kanaf)
            
            reply = ''
            
            if len(command) > 2:
                reply = '```'
                
                if command[2].lower() == 'hiragana':
                    for set in kana["hiragana"]:
                        for entry in kana["hiragana"][set]:
                            reply += entry[0] + ' '
                        reply += '\n'
                    reply += '```'
                elif command[2].lower() == 'katakana':
                    for set in kana["katakana"]:
                        for entry in kana["katakana"][set]:
                            reply += entry[0] + ' '
                        reply += '\n'
                    reply += '```'
                else:
                    reply = 'Unknown character set.'
            
            else:
                reply+= '```Hiragana:\n'
                for set in kana["hiragana"]:
                    for entry in kana["hiragana"][set]:
                        reply += entry[0] + ' '
                    reply += '\n'

                reply += '\nKatakana:\n'
                for set in kana["katakana"]:
                    for entry in kana["katakana"][set]:
                        reply += entry[0] + ' '
                    reply += '\n'
                reply += '```'
                
                
            await message.channel.send(reply)
            
        
def initialize(guild):
    conn = sqlite3.connect(settings.database(guild))
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE timezones(id INTEGER PRIMARY KEY AUTOINCREMENT, tzname TEXT)")
    print('\'timezones\' table created.')
    for tz in pytz.all_timezones:
        cursor.execute("INSERT INTO timezones(tzname) VALUES (?)", (tz,))
    print('\'timezones\' table populated.')
    cursor.execute("ALTER TABLE users ADD timezone INTEGER DEFAULT '581'")
    print('\'timezone\' field added to \'users\' table.')
    cursor.execute("CREATE TABLE studysessions(id INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER, datestudied TEXT, streak INTEGER)")
    print('\'studysessions\' table created.')
    
    conn.commit()
    conn.close()
    
# def checkdate(inputstring, inputmember):

    # conn = sqlite3.connect(settings.database(inputmember.guild))
    # cursor = conn.cursor()
    # cursor.execute("SELECT timezones.tzname FROM users JOIN timezones ON users.timezone = timezones.id WHERE users.id = ?", (inputmember.id,))
    # usertz = cursor.fetchone()
    # conn.close()
    # today = datetime.datetime.now(pytz.timezone(usertz[0])).date()
    
    # validity = await utilities.checkdate(inputstring, today)
    # print(type(validity))
    # reply = 'uhhhhh'
    
    #if type(validity)
    
    # if len(inputstring) <= 2:
        # try:
            # reply = datetime.date(today.year, today.month, int(inputstring))
        # except ValueError:
             # reply = '```That is not a valid day for this month.```'

    # elif len(inputstring) > 7:
        # inputtext = inputstring.split("-")

        # try:
            # reply = datetime.datetime.strptime(inputstring, '%Y-%m-%d').date()

        # except ValueError:
            # try:
                # if int(inputtext[1]) > 0 and int(inputtext[1]) <= 12:
                    # monthlen = calendar.monthrange(int(inputtext[0]), int(inputtext[1]))
                    # if int(inputtext[2]) > monthlen[1]:
                        # reply = '```There are only %s days in %s.```' % (monthlen[1], datetime.date(today.year, int(inputtext[1]), 1).strftime('%B'))
                    # else:
                        # reply = '```That is not a valid date```.'
                # else:
                    # reply = '```That is not a valid month.```'
            # except ValueError:
                # reply = '```That is not a valid date.```'
            
        # except IndexError:
            # reply = '```Date not in an acceptable format. Please type date as either a day of the current month, or a full date in the YYYY-MM-DD format.```'
    # else:
        # reply = '```Unrecognized parameter.```'

   # return reply
    
    
def drawcalendar(inputuser, message, inputdate):
    monthname = inputdate.strftime('%B')
    monthdays = calendar.monthrange(inputdate.year, inputdate.month)

    leadspace = math.ceil((17 - len(monthname))/2)
    
    textcalendar = '```' + ' '*leadspace + monthname + ' ' + str(inputdate.year) + '\n'
    
    if monthdays[0] < 6:
        textcalendar = textcalendar + '   '*(monthdays[0] + 1)
        weekd = monthdays[0] + 2
    else:
        weekd = 1
    
    i = 1
    r = 0
    while i <= monthdays[1]:
        iterdate = datetime.date(inputdate.year, inputdate.month, i)
        
        conn = sqlite3.connect(settings.database(message.guild))
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM studysessions WHERE userid = ? AND datestudied LIKE ?", (inputuser.id, iterdate.strftime('%Y-%m-') + '%'))
        monthcount = cursor.fetchone()
        percentstudied = int((monthcount[0]/monthdays[1])*100)

        cursor.execute("SELECT datestudied FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, iterdate))
        tdstudy = cursor.fetchone()
        cursor.execute("SELECT datestudied FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, iterdate - datetime.timedelta(days=1)))
        ydstudy = cursor.fetchone()
        cursor.execute("SELECT datestudied FROM studysessions WHERE userid = ? AND datestudied = ?", (inputuser.id, iterdate + datetime.timedelta(days=1)))
        tmstudy = cursor.fetchone()
        conn.close()
        
        if i < 10:
            if tdstudy and ydstudy:
                textcalendar = textcalendar + '~'
            elif ydstudy and not tdstudy and weekd > 1 and i > 1:
                textcalendar = textcalendar + '>'
            else:
                textcalendar = textcalendar + ' '
        
        if tdstudy and ydstudy:
            textcalendar = textcalendar + '~' + str(i)
        elif tdstudy and not ydstudy:
            textcalendar = textcalendar + '<' + str(i)
        elif ydstudy and i > 9 and not tdstudy and weekd > 1:
            textcalendar = textcalendar + '>' + str(i)
        else:
            textcalendar = textcalendar + ' ' + str(i)
        
        if weekd > 6:
            
            if tdstudy and tmstudy:
                textcalendar = textcalendar + '~'
            elif tdstudy and not tmstudy:
                textcalendar = textcalendar + '>'
            else:
                textcalendar = textcalendar + ' '
                
            if r == 2:
                
                textcalendar = textcalendar + '\t' + str(monthcount[0]) + '/' + str(monthdays[1]) + ' days studied'
            
            if r == 3:
                textcalendar = textcalendar + '\t' + str(percentstudied) + '% complete'
                
            weekd = 0
            r += 1
            textcalendar = textcalendar + '\n'
        
        weekd += 1
        i += 1
    
    
    if weekd > 1:
        if tdstudy:
            if tmstudy:
                textcalendar = textcalendar + '~\n'
            else:
                textcalendar = textcalendar + '>\n'
        else:
            textcalendar = textcalendar + '\n'
    
    textcalendar = textcalendar + '<> Study Log  ~ Streak```'
    
    return textcalendar
    
async def interactive_emotes(reaction, user, session):
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
        
async def kana_game(set, message):
    return
            
    # emoji_a = '\U0001F1E6'
    # emoji_b = '\U0001F1E7'
    # emoji_c = '\U0001F1E8'
    # emoji_d = '\U0001F1E9'
    
    # with open(settings.datapath + 'kana.json', 'r') as kanaf:
        # kana = json.load(kanaf)
        
    # randomset = []
    # wronganswers = []
    
    # if set == 'hiragana':
        # for group in kana["hiragana"]:
            # for entry in kana["hiragana"][group]:
                # randomset.append(entry)
    
    # elif set == 'katakana':
        # for group in kana["katakana"]:
            # for entry in kana["katakana"][group]:
                # randomset.append(entry)
                
    # elif set == 'full':
        # for lib in kana:
            # for group in kana[lib]:
                # for entry in kana[lib][group]:
                    # randomset.append(entry)
    
    # for item in randomset:
        # wronganswers.append(item[1])
    
    # random.shuffle(randomset)
    # random.shuffle(wronganswers)
    
    # question = randomset.pop()
    
    # answers = [question[1]]
    
    # while len(answers) < 4:
        # next = wronganswers.pop()
        # while next in answers:
            # next = wronganswers.pop()
            
        # answers.append(next)
    
    # random.shuffle(answers)
    
    # i = 0
    # while i < 4:
        # if answers[i] == question[1]:
            # correct = i
    
    # kanaquestion(
    
    
    # qtext = '```' + question[0] + '\n'
    
    # qtext += '\nA: ' + answers[0]
    # qtext += '\nB: ' + answers[1]
    # qtext += '\nC: ' + answers[2]
    # qtext += '\nD: ' + answers[3]

    # qtext += '```'
    
    # sent = await message.channel.send(qtext)
    
    # packdata = correct + ';;
    
    # conn = sqlite3.connect(settings.database(message.channel.guild))
    # cursor = conn.cursor()
    # cursor.execute("INSERT INTO commanddata(user, message, type, data) VALUES (?, ?, ?, ?)", (message.author.id, sent.id, 'kanagame', 1))
    # conn.commit()
    # conn.close()
    
    # await sent.add_reaction(emoji_a)
    # await sent.add_reaction(emoji_b)
    # await sent.add_reaction(emoji_c)
    # await sent.add_reaction(emoji_d)
    
async def kana_game_watchdog(message):
    timeout = False
    
    while timeout == False:
        conn = sqlite3.connect(settings.database(message.channel.guild))
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM commanddata WHERE user = ?", (message.author.id,))
        A = cursor.fetchone()
        conn.close()
        
        if A:
            await asyncio.sleep(5)
        
            conn = sqlite3.connect(settings.database(message.channel.guild))
            cursor = conn.cursor()
            cursor.execute("SELECT message FROM commanddata WHERE user = ?", (message.author.id,))
            B = cursor.fetchone()
            conn.close()
        
            if B:
                if A == B:
                    timeout = True
            
            else:
                return
        else:
            return
    
    await message.channel.send('kanagame timed out!')
    conn = sqlite3.connect(settings.database(message.guild))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM commanddata WHERE type = 'kanagame'")
    conn.commit()
    conn.close()
