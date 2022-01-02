## Discord Bot Online Judge
This is a discord bot made using Discord's python library that
runs and judges solutions for competitive programming problems. It also has the ability to host contests.

To join the bot's official discord server: https://discord.gg/mhJbxatSpS

To add problems to the judge, visit: https://docs.google.com/document/d/1dC3KeeH4XU5Dl6ijnfIUP6wjhv2YWg0lSkpkgrRJJA0/edit?usp=sharing

To add the bot to your own discord server: https://discord.com/api/oauth2/authorize?client_id=831963122448203776&permissions=2148005952&scope=bot

Once the bot is in your server, run the `-help` command to get a list of commands and a tutorial for the bot.

Check out the bot on Discord Bot List and top.gg: https://discordbotlist.com/bots/judge, https://top.gg/bot/831963122448203776

## Cloning the judge
### 1. Clone this repository
```bash
sudo apt-get install git
git clone https://github.com/DiscordBotOnlineJudge/discord-bot-interface.git
cd discord-bot-interface
```

### 2. Install the python dependencies
If you haven't already, install python3's pip installer using:
```bash
sudo apt-get install python3-pip
```
Install all the dependencies from the `requirements.txt` file
```bash
python3 -m pip install -r requirements.txt
```

### 3. Set the required environment variables
```bash
export TOKEN=[your discord bot token]
export PASSWORD=[your full mongodb connection string]
```

### 4. Paste your google cloud credentials
Create a service account in your google cloud that **only** gives access to storage buckets:
```
storage.buckets.get
storage.objects.create
storage.objects.delete
storage.objects.get
```
Paste the key json into a file called `google-service-key.json`.

### 5. Setting up mongodb and google cloud storage
Pymongo needs to have pre-made registers for languages and judges.
The language register should look like this:
```
_id: [any object id]
type: "lang"
name: [language name]
compl: [command to compile the file or leave empty string for non-compiled]
run: [command to execute the code]
filename: [the name of the file to save to]
id: [language id from 0 to 2 based on speed of language (0 is slow, 2 is fast)]
```

The judge register should look like this. Instructions to create a judge server are [here](https://github.com/DiscordBotOnlineJudge/judge-server).
```
_id: [any object id]
type: "judge"
num: [judge number]
status: 0
output: ""
ip: "[the ip address of the judge server or localhost]"
path: [full path of the judge-server repository in the judge server (e.g. "/home/ubuntu/judge-server")]
port: [the port number that the judge server is listening on]
description: [a description of the judge server]
runtimes: [description of runtimes of the judge server]
```

The google-cloud storage bucket should be named `discord-bot-oj-file-storage`. The bot will add its own folders as you add problems and contests.

### 6. Start the Discord bot server using python
```bash
python3 main.py
```
