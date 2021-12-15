# Online Judge Discord Bot
# Main python executable

import time
import discord
import os
import sys
import subprocess
import math
import dns
import asyncio
import judging
import contests
import requests
import secrets
import string
import grpc
import judge_pb2
import judge_pb2_grpc
import ProblemUpload
from multiprocessing import Process
from multiprocessing import Manager
from google.cloud import storage
from functools import cmp_to_key
from pymongo import MongoClient

client = discord.Client()

def writeCode(source, filename):
    f = open(filename, "w")
    f.write(source)
    f.close()
        
def clearFile(filename):
    os.remove(filename)

def clearSources(judgeNum):
    try:
        clearFile("Judge" + str(judgeNum) + "/data.out")
    except:
        print("Failed to remove output file")

def decode(cde):
    if cde == 0:
        return "Available"
    elif cde == 1:
        return "Submission in Progress"
    elif cde == 2:
        return "Offline"
    else:
        return ""

def generatePassword():
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(13))
    return password

def clean(src):
    return src.replace("`", "")

def getLen(contest):
    return settings.find_one({"type":"contest", "name":contest})['len']

def perms(found, author):
    acc = settings.find_one({"type":"access", "mode":found['contest'], "name":author})
    if (not settings.find_one({"type":"access", "mode":"owner", "name":author}) is None):
        return False # Has owner perms
    if (not settings.find_one({"type":"access", "mode":"admin", "name":author}) is None) and (author in found['authors']):
        return False # Has admin perms
    elif (not acc is None) and (found['status'] == "s") and contests.compare(acc['start'], contests.current_time()) <= getLen(found['contest']):
        return False # Has contest participant perms
    return (not found['published']) or (found['status'] != "s")

def getStatus():
    msg = ""
    for x in settings.find({"type":"judge"}):
        msg += "Judge #" + str(x['num']) + ": " + decode(x['status']).ljust(23)
        if x['status'] != 2:
            msg += "(" + x['runtimes'] + ")"
        msg += "\n"
    return msg

async def updateStatus():
    msg = getStatus()
    global status
    try:
        await status.edit(content = ("**Current live judge server statuses:**\n```" + getStatus() + "\n```"))
    except:
        print("Failed to update live status")
        return

def amt(len):
    h = len // 3600
    len %= 3600
    m = len // 60
    len %= 60
    s = len

    return "{hh} hours, {mm} minutes, and {ss} seconds".format(hh = h, mm = m, ss = s)

def profile(name):
    prof = settings.find_one({"type":"profile", "name":name})
    if prof is None:
        return (name + " has not solved any problems yet.")
    a = "Problems fully solved by `" + name + "`:\n```"
    cnt = 0
    for x in prof['solved']:
        p = settings.find_one({"type":"problem", "name":x})
        if p is None or not p['published']:
            continue
        a += x + " (" + str(p['points']) + " points)\n"
        cnt += 1
    if cnt <= 0:
        return (name + " has not solved any problems yet.")
    return a + "```" + str(cnt) + " problems solved in total"

def addToProfile(name, problem):
    if settings.find_one({"type":"profile", "name":name}) is None:
        settings.insert_one({"type":"profile", "name":name, "solved":[]})
    settings.update_one({"type":"profile", "name":name}, {"$addToSet":{"solved":problem}})

def cmp(a, b):
    if a[1] != b[1]:
        return b[1] - a[1]
    return a[2] - b[2]

def cmpProblem(a, b):
    return a[0] - b[0]

def getScoreboard(contest):
    ct = settings.find_one({"type":"contest", "name":contest})
    if ct is None:
        return "Contest not found!"

    time_bonus = ct['has-time-bonus']
    penalty = ct['has-penalty']

    fnd = settings.find({"type":"access", "mode":contest})
    arr = [x for x in fnd]

    msg = "**Current rankings for participants in contest `" + contest + "`**\n```"
    cnt = 0

    namWid = 0
    pWid = [0] * (ct['problems'] + 1)
    comp = []

    for x in arr:
        namWid = max(namWid, len(x['name']))
        for y in range(1, len(x['solved'])):
            dt = "P" + str(y) + "-" + str(x['solved'][y])

            if time_bonus and x['time-bonus'][y] > 0:
                dt += "(+" + str(x['time-bonus'][y]) + ")"
            if penalty and x['penalty'][y] > 0:
                dt += "(" + str(x['penalty'][y]) + ")"
            pWid[y] = max(pWid[y], len(dt))
    for x in arr:
        m = x['name'].ljust(namWid) + " : "
        total = 0
        for y in range(1, len(x['solved'])):
            dt = "P" + str(y) + "-" + str(x['solved'][y])

            if time_bonus and x['time-bonus'][y] > 0:
                dt += "(+" + str(x['time-bonus'][y]) + ")"
            if penalty and x['penalty'][y] > 0:
                dt += "(" + str(x['penalty'][y]) + ")"
                
            m += dt.ljust(pWid[y]) + " "
            total += x['solved'][y] + x['time-bonus'][y]
        m += "total: " + str(total)
        comp.append((m, total, sum(x['penalty'])))
    
    comp.sort(key = cmp_to_key(cmp))
    idx = 0
    cur = 0
    for i in range(len(comp)):
        cur += 1
        if i == 0 or comp[i - 1][1] != comp[i][1] or comp[i - 1][2] != comp[i][2]:
            idx = cur
        msg += str(idx) + ") " + comp[i][0] + "\n"

    if len(comp) <= 0:
        msg += "---No participants are in this contest yet---\n"
        
    return msg + "```"

async def live_scoreboard(contest):
    global scb
    current_contest = settings.find_one({"type":"livecontests"})['arr']
    for x in range(len(current_contest)):
        if current_contest[x] == contest:
            await scb[x].edit(content = getScoreboard(contest))
            return
    print("Failed to update live scoreboard")

def get_bonus(rem, pts):
    return (pts * rem) // 30000

async def updateScore(contest, problem, user, score, ct):
    post = settings.find_one({"type":"access", "name":user, "mode":contest})
    if post is None:
        print("Failed to update score (no access post)")
        return
    elapsed = contests.compare(post['start'], ct)
    contest_len = getLen(contest)
    if elapsed > contest_len:
        print("Invalid score update")
        return
    arr = post['solved']
    penalty = post['penalty']
    time_bonus = post['time-bonus']

    num = int(problem[len(problem) - 1])

    if score <= arr[num] and arr[num] < 100:
        penalty[num] += 1
    if arr[num] < 100:
        settings.update_one({"_id":post['_id']}, {"$set":{"taken":elapsed}})

    arr[num] = max(arr[num], score)
    time_bonus[num] = max(time_bonus[num], get_bonus(contest_len - elapsed, score))

    settings.update_one({"_id":post['_id']}, {"$set":{"solved":arr, "penalty":penalty, "time-bonus":time_bonus}})
    await live_scoreboard(contest)

def remaining(name):
    acc = settings.find({"type":"access", "name":name})
    msg = ""
    for x in acc:
        if x['mode'] != "admin" and x['mode'] != "owner":
            try:
                total = getLen(x['mode'])
                elapsed = contests.compare(x['start'], contests.current_time())
                rem = total - elapsed
                if rem <= 0:
                    msg += "Time's up! `" + name + "`'s participation in contest `" + x['mode'] + "` has ended.\n"
                else:
                    msg += "`" + name + "` still has `" + amt(rem) + "` left on contest `" + x['mode'] + "`\n"
            except:
                pass
    if len(msg) == 0:
        return "`" + name + "` has not joined any contests"
    return msg

async def sendLiveScoreboards():
    current_contest = settings.find_one({"type":"livecontests"})['arr']

    global scb
    scb = [None] * len(current_contest)
    sbc = client.get_channel(852311780378148914)
    await sbc.purge(limit = 100)

    for x in range(len(current_contest)):
        scb[x] = await sbc.send(getScoreboard(current_contest[x]))

def runSubmission(judges, username, cleaned, lang, problm, attachments, return_dict):
    with grpc.insecure_channel(judges['ip'] + ":" + str(judges['port'])) as channel:
        stub = judge_pb2_grpc.JudgeServiceStub(channel)
        response = stub.judge(judge_pb2.SubmissionRequest(username = username, source = cleaned, lang = lang, problem = problm['name'], attachment = attachments))
        finalscore = response.finalScore
        return_dict['finalscore'] = finalscore

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="-help"))

    global storage_client
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-service-key.json'
    stc = storage.Client()
    storage_client = stc.get_bucket('discord-bot-oj-file-storage')

    pswd = open("PASSWORD", "r").read().strip()

    cluster = MongoClient("mongodb+srv://onlineuser:$" + pswd + "@discord-bot-online-judg.7gm4i.mongodb.net/database?retryWrites=true&w=majority")
    db = cluster['database']
    global settings
    settings = db['settings']

    global running
    running = True

    global status
    stat = client.get_channel(851468547414294568)
    await stat.purge(limit = 100)
    status = await stat.send("**Current live judge server statuses:**\n```" + getStatus() + "\n```")

    await sendLiveScoreboards()

    #chnl = client.get_channel(846768989211197510)
    #await chnl.send("Judge has connected to Discord!")
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    global settings
    global running
    global status
    global storage_client
    req = settings.find_one({"type":"req", "user":str(message.author), "used":False})

    if str(message.content).startswith("-"):
        for x in settings.find({"type":"command"}):
            if str(message.content).startswith(x['name']):
                settings.insert_one({"type":"use", "author":str(message.author), "message":str(message.content)})
                break

    if not str(message.content).startswith("-") and (not req is None):
        try:
            ct = contests.current_time()

            username = req['user']
            problem = req['problem']
            lang = req['lang']

            settings.delete_one({"type":"prev", "name":username})
            settings.insert_one({"type":"prev", "name":username, "problem":problem, "lang":lang})

            problm = settings.find_one({"type":"problem", "name":problem})

            judges = settings.find_one({"type":"judge", "num":req['judge']})
            if "judge" in req and not judges is None and judges['status'] == 0:
                judges = settings.find_one({"type":"judge", "num":req['judge']})
            else:
                judges = settings.find_one({"type":"judge", "status":0})

            if judges is None:
                await message.channel.send("All of the judge's grading servers are currently in use. Please re-enter your source code in a few seconds.\nType `-status` to see the current judge statuses")
                return

            settings.update_one({"_id":req['_id']}, {"$set":{"used":True}})
            settings.update_one({"_id":judges['_id']}, {"$set":{"status":1}})
            settings.delete_one({"_id":req['_id']})

            await updateStatus()

            avail = judges['num']

            cleaned = ""
            attachments = False
            if message.attachments:
                cleaned = message.attachments[0].url
                attachments = True
            else:
                # Clean up code from all backticks
                cleaned = clean(str(message.content))

            settings.insert_one({"type":"use", "author":str(message.author), "message":cleaned})
            await message.channel.send("Now judging your program. Please wait a few seconds.")

            manager = Manager()
            return_dict = manager.dict()
            rpc = Process(target = runSubmission, args = (judges, username, cleaned, lang, problm, attachments, return_dict,))
            rpc.start()

            msgContent = "```Waiting for response from Judge " + str(avail) + "```"
            curmsg = await message.channel.send(msgContent)

            while rpc.is_alive():
                newcontent = settings.find_one({"type":"judge", "num":avail})['output']
                if newcontent != msgContent and len(newcontent) > 0:
                    msgContent = newcontent
                    try:
                        await curmsg.edit(content = msgContent)
                    except:
                        print("Edited empty message")
                await asyncio.sleep(0.5)

            try:
                finalscore = return_dict['finalscore']
                await curmsg.edit(content = settings.find_one({"type":"judge", "num":avail})['output'])
                if finalscore == 100:
                    addToProfile(str(message.author), problem)
                if len(problm['contest']) > 0 and finalscore >= 0:
                    await updateScore(problm['contest'], problem, str(message.author), finalscore, ct)
            except Exception as e:
                await message.channel.send("Judging error: Fatal error occured on Judge Server " + str(avail) + " while grading solution")
                print(e)
            
            settings.update_one({"_id":judges['_id']}, {"$set":{"output":""}})
        except Exception as e:
            await message.channel.send("Judging error: Fatal error occured while grading solution\n```" + str(e) + "\n```")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        settings.update_one({"_id":judges['_id']}, {"$set":{"status":0}})
        await updateStatus()

    else:
        if len(str(message.content)) <= 0:
            return

        if message.content == "-help":
            await message.channel.send("**Here are some of my commands:**")
            f = open("commands.txt", "r")
            await message.channel.send("```" + str(f.read()) + "```")
        elif message.content.startswith("-problem"):
            w1 = 14
            out = "Problem Name".ljust(w1) + "Difficulty\n"
            out += "-----------------------------------------------\n"
            
            arr = sorted([(x['points'], x['name']) for x in settings.find({"type":"problem", "published":True})], key = cmp_to_key(cmpProblem))
            
            for x in arr:
                out += x[1].ljust(w1) + (str(x[0]) + " points") + "\n"

            out += "\n"

            f = open("problems.txt", "r")
            out += f.read()
            f.close()
            await message.channel.send("All published problems:\n```\n" + out + "```")

        elif str(message.content).split()[0].startswith("-sub"):
            arr = str(message.content).split()

            if len(arr) < 3:
                await message.channel.send("Incorrect formatting for submit command. Please type `-submit [problemName] [language]` and wait for the judge to prompt you for your source code.")
                return

            problem = arr[1].lower()
            language = arr[2].lower()

            found = settings.find_one({"type":"problem", "name":problem})
            if found is None or (perms(found, str(message.author))):
                await message.channel.send("Judging Error: Problem not found. The problem may either be private or does not exist.")
                return

            lang = settings.find_one({"type":"lang", "name":language})
            if lang is None:
                await message.channel.send("Judging Error: Language not Found. Type `-langs` for a list of supported languages.")
                return

            judge = 0
            if not settings.find_one({"type":"access", "mode":"admin", "name":str(message.author)}) is None and len(arr) > 3:
                try:
                    judge = int(arr[3])
                except:
                    pass

            settings.insert_one({"type":"req", "user":str(message.author), "problem":problem, "lang":language, "used":False, "judge":judge})
            await message.channel.send("Submission request received from `" + str(message.author) + "` for problem `" + problem + "` in `" + language + "`.\nSend your source code either as an attachment or a message surrounded by backticks (`).")
        elif str(message.content).startswith("-rs"):
            arr = str(message.content).split()
            prev = settings.find_one({"type":"prev", "name":str(message.author)})
            if prev is None:
                await message.channel.send("No previous submission found. Please type `-submit [problemName] [language]` to submit a submission.")
                return

            if perms(settings.find_one({"type":"problem", "name":prev['problem']}), str(message.author)):
                await message.channel.send("Judging Error: Problem not found. The problem may either be private or does not exist.")
                return

            language = None
            if len(arr) < 2:
                settings.insert_one({"type":"req", "user":str(message.author), "problem":prev['problem'], "lang":prev['lang'], "used":False})
                language = prev['lang']
            else:
                lang = settings.find_one({"type":"lang", "name":arr[1]})
                if lang is None:
                    await message.channel.send("Judging Error: Language not Supported. Type `-langs` for a list of supported languages.")
                    return
                settings.insert_one({"type":"req", "user":str(message.author), "problem":prev['problem'], "lang":arr[1], "used":False})
                language = arr[1]
            await message.channel.send("Submission request received from `" + str(message.author) + "` for problem `" + prev['problem'] + "` in `" + language + "`.\nSend your source code either as an attachment or a message surrounded by backticks (`).")
        elif str(message.content).split()[0].startswith("-lang"):
            judging.get_file(storage_client, "Languages.txt", "Languages.txt")
            f = open("Languages.txt", "r")
            msg = f.read()
            await message.channel.send(msg + "\nTo see exact execution commands, visit https://dboj.jimmyliu.dev/")
        elif str(message.content).startswith("-error"):
            f = open("errors.txt", "r")
            await message.channel.send("```\n" + f.read(5000) + "\n```")
        elif str(message.content).split()[0] == "-open":
            # perm = settings.find_one({"type":"access", "name":str(message.author)})
            prob = settings.find_one({"type":"problem", "name":str(message.content).split()[1].lower()})

            if prob is None or perms(prob, str(message.author)):
                await message.channel.send("Error: Problem not found")
                return

            try:
                judging.get_file(storage_client, "ProblemStatements/" + prob['name'] + ".txt", "ProblemStatement.txt")
                ps = open("ProblemStatement.txt", "r")
                st = ps.read()
                await message.channel.send(st)
            except Exception as e:
                await message.channel.send("An error occured while retrieving the problem statement:\n```" + str(e) + "\n```")
        elif str(message.content).split()[0] == "-reset":
            if str(message.author) != "jiminycricket#2701":
                await message.channel.send("Sorry, you do not have authorized access to this command.")
                return

            settings.update_many({"type":"judge", "status":1}, {"$set":{"status":0}})
            await updateStatus()
            await message.channel.send("All servers' statuses are now set to available")
        elif str(message.content).startswith("-add"):
            await message.channel.send("To add your own problem to the judge, visit this site: https://dboj.jimmyliu.dev/")
        elif str(message.content).startswith("-vote"):
            await message.channel.send("Vote for the Judge discord bot!\nDiscord Bot List: https://discordbotlist.com/bots/judge/upvote\ntop.gg: https://top.gg/bot/831963122448203776/vote\n\nThanks for your support!")
        elif str(message.content).startswith("-server"):
            msg = "Discord bot online judge is currently in " + str(len(client.guilds)) + " servers!"
            if str(message.channel) == "Direct Message with jiminycricket#2701":
                msg += "\n```\n"
                for x in client.guilds:
                    msg += str(x) + "\n"
                await message.channel.send(msg + "```")
            else:
                await message.channel.send(msg)
        elif str(message.content).split()[0] == "-users":
            if str(message.channel) != "Direct Message with jiminycricket#2701":
                return
            f = open("users.txt", "r")
            await message.channel.send("```\n" + f.read() + "```")
            f.close()
        elif str(message.content).startswith("-on"):
            j = int(str(message.content).split()[1])
            settings.update_one({"type":"judge", "num":j}, {"$set":{"status":0}})
            await updateStatus()
            await message.channel.send("Judge " + str(j) + " is now online")
        elif str(message.content).startswith("-off"):
            j = int(str(message.content).split()[1])
            settings.update_one({"type":"judge", "num":j}, {"$set":{"status":2}})
            await updateStatus()
            await message.channel.send("Judge " + str(j) + " is now offline")
        elif str(message.content) == "-status":
            msg = getStatus()
            await message.channel.send("**Current Judge Server Statuses:**\n```\n" + msg + "```")
        elif str(message.content).startswith("-reset"):
            settings.update_many({"type":"judge"}, {"$set":{"status":0}})
            await updateStatus()
            await message.channel.send("All online judging servers successfully reset.\nType `-status` to see current judge statuses")
        elif str(message.content).startswith("-invite"):
            await message.channel.send("Invite the online judge discord bot to your own server with this link: \nhttps://discord.com/api/oauth2/authorize?client_id=831963122448203776&permissions=2148005952&scope=bot")
        elif str(message.content).startswith("-cancel"):
            settings.delete_many({"type":"req"})
            await message.channel.send("Successfully cancelled all active submission requests")
        elif str(message.content) == "-sigterm":
            running = False # set terminate signal
            await message.channel.send("Attempting to terminate processes.")
        elif str(message.content) == "-sigkill":
            await message.channel.send("Killing process signal using system exiter.")
            exit(0) # Kill using system exit function
        elif str(message.content) == "-restart":
            running = True # Attempt to restart process
            await message.channel.send("Restarting judge.")
        elif str(message.content).startswith("-join"):
            if not (str(message.channel).startswith("ticket-") or str(message.channel).endswith("-channel")):
                await message.channel.send("Please join contests in a private channel with the bot. Head to <#855868243855147030> to create one.")
                return

            arr = str(message.content).split()
            if len(arr) != 2:
                await message.channel.send("Incorrect formatting for join command. Use `-join [contestCode]` to join a contest")
                return
            cont = settings.find_one({"type":"contest", "name":arr[1].lower()})
            if cont is None:
                await message.channel.send("Error: Contest not found")
                return
            if (not contests.date(cont['start'], cont['end'], contests.current_time())):
                await message.channel.send("This contest is not currently active. Type `-up` to see upcoming contest times.")
                return
            if not settings.find_one({"type":"access", "mode":arr[1], "name":str(message.author)}) is None:
                await message.channel.send("You already joined this contest!")
                return

            solved = [0] * (cont['problems'] + 1)
            penalties = [0] * (cont['problems'] + 1)
            time_bonus = [0] * (cont['problems'] + 1)

            settings.insert_one({"type":"access", "mode":arr[1], "name":str(message.author), "solved":solved, "penalty":penalties, "time-bonus":time_bonus, "start":contests.current_time(), "taken":0})
            await live_scoreboard(arr[1])

            await message.channel.send("Successfully joined contest `" + arr[1] + "`! You have " + amt(cont['len']) + " to complete the contest. Good Luck!\n")
            await asyncio.sleep(1)
            judging.get_file(storage_client, "ContestInstructions/" + arr[1] + ".txt", "ContestInstructions.txt")
            f = open("ContestInstructions.txt", "r")
            await message.channel.send("```\n" + f.read() + "\n```")

            notif = client.get_channel(858365776385277972)
            await notif.send("<@627317639550861335> User `" + str(message.author) + "` joined contest `" + arr[1] + "`!")

        elif str(message.content).startswith("-profile"):
            arr = str(message.content).split()
            if len(arr) == 1:
                await message.channel.send(profile(str(message.author)))
            else:
                await message.channel.send(profile(str(message.content)[9:]))
        elif str(message.content).startswith("-rank"):
            arr = str(message.content).split()
            if len(arr) < 2:
                await message.channel.send("Incorrect formatting for `-rank` command. Please type `-rank [contestCode]` for the scoreboard")
            else:
                await message.channel.send(getScoreboard(arr[1]))
        elif str(message.content).startswith("-rem"):
            arr = str(message.content).split()
            if len(arr) == 1:
                await message.channel.send(remaining(str(message.author)))
            else:
                await message.channel.send(remaining(str(message.content)[5:]))
        elif str(message.content).startswith("-up"):
            m = "Upcoming contests:\n```"
            f = False
            for x in settings.find({"type":"contest"}):
                if contests.compString(x['end'], contests.current_time()):
                    m += "Contest " + x['name'] + " starts at " + x['start'] + " and ends at " + x['end'] + "\n"
                    f = True
            if not f:
                m += "No upcoming contests\n"
            m += "```"
            await message.channel.send(m)
        elif str(message.content).startswith("-refresh"):
            arr = str(message.content).split()
            if len(arr) < 2:
                await message.channel.send("Incorrect formatting for refresh command. Use `-refresh [contestCode]`")
                return

            for i in range(1, len(arr)):
                await live_scoreboard(arr[i])
                
            await updateStatus()
            await message.channel.send("Refreshed live scoreboard and live judge status")
        elif str(message.content).startswith("-set"):
            arr = str(message.content).split()
            
            if settings.find_one({"type":"access", "mode":"admin", "name":str(message.author)}) is None:
                await message.channel.send("Sorry, you do not have sufficient permissions to use this command.")
                return

            settings.update_one({"type":"livecontests"}, {"$set":{"arr":arr[1:]}})
            await sendLiveScoreboards()
            await message.channel.send("Live scoreboard contests set to `" + str(arr[1:]) + "`")
        elif str(message.content).startswith("-console"):
            if settings.find_one({"type":"access", "mode":"admin", "name":"jiminycricket#2701"}) is None:
                await message.channel.send("Sorry, you do not have sufficient permissions to use this command.")
                return
            output = open("console.out", "w")
            tm = float(str(message.content).split()[1])
            console = subprocess.Popen(str(message.content)[(str(message.content).find("$")+1):], stdout=output, preexec_fn = judging.limit_virtual_memory, shell=True)
            await message.channel.send("Console started. Running command `" + str(message.content)[(str(message.content).find("$")+1):] + "` for " + str(tm) + " second(s).")
            
            try:
                console.wait(timeout = tm)
            except subprocess.TimeoutExpired:
                console.terminate()

            output.flush()
            output.close()

            await message.channel.send("Console finished. Output shown below:\n```" + open("console.out", "r").read(2000) + "\n```")
        elif str(message.content).startswith("-export"):
            if settings.find_one({"type":"access", "mode":"admin", "name":"jiminycricket#2701"}) is None:
                await message.channel.send("Sorry, you do not have sufficient permissions to use this command. Please contact jiminycricket#2701 for problem setting permissions.")
                return
            if len(message.attachments) == 0:
                await message.channel.send("Please attach a zip archive with the problem info along with the `-export` command")
                return
            
            await message.channel.send("Uploading problem data...")
            try:
                msg = ProblemUpload.uploadProblem(settings, storage.Client(), str(message.attachments[0]), str(message.author))
                await message.channel.send(msg)
            except Exception as e:
                await message.channel.send("Error occurred while uploading problem data:\n```" + str(e) + "\n```")
            
            os.system("rm -r problemdata; rm data.zip")
        elif str(message.content) == "-register":
            if not str(message.channel).startswith("Direct Message with"):
                await message.channel.send("Please use `-register` in a direct message with the bot.")
                return
            if settings.find_one({"type":"account", "name":str(message.author)}) is not None:
                await message.channel.send("An account under your username has already been registered. If you forgot your password, please contact me (`jiminycricket#2701`).")
                return
            pswd = generatePassword()
            settings.insert_one({"type":"account", "name":str(message.author), "pswd":pswd})
            await message.channel.send("Your account has been successfully created! Your password is `" + pswd + "`. Please don't share it with anyone.")
            

with open("TOKEN", "r") as f:
    client.run(f.read().strip())