import os
import json
from google.oauth2 import service_account
from discord.ext import commands
from googleapiclient.discovery import build
import discord

from dotenv import load_dotenv
load_dotenv()

# Load credentials from env
credentials = service_account.Credentials.from_service_account_file(os.environ["GCP_CREDENTIALS_JSON"])

GCP_PROJECT = os.environ["GCP_PROJECT_ID"]
GCP_ZONE = os.environ["GCP_ZONE"]
GCP_INSTANCE = os.environ["GCP_INSTANCE"]
DISCORD_TOKEN = os.environ["DSC_BOT_TOKEN"]

compute = build("compute", "v1", credentials=credentials)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def startserver(ctx):
    await ctx.send("🚀 Starting Palworld server...")

    compute.instances().start(
        project=GCP_PROJECT,
        zone=GCP_ZONE,
        instance=GCP_INSTANCE
    ).execute()

    # Wait for VM to be in RUNNING state
    import time
    status = "PROVISIONING"
    while status != "RUNNING":
        time.sleep(5)
        instance = compute.instances().get(
            project=GCP_PROJECT,
            zone=GCP_ZONE,
            instance=GCP_INSTANCE
        ).execute()
        status = instance["status"]
        print(f"Waiting for VM... Status = {status}")

    # Get external IP
    ip = instance["networkInterfaces"][0]["accessConfigs"][0]["natIP"]

    await ctx.send(f"✅ Server is now **{status}**\n🌐 Connect via IP: `{ip}:8211`\n🔒Password: `8739`")

@bot.command()
async def stopserver(ctx):
    await ctx.send("🛑 Shutting down Palworld server...")

    compute.instances().stop(
        project=GCP_PROJECT,
        zone=GCP_ZONE,
        instance=GCP_INSTANCE
    ).execute()

    # Wait for the VM to fully stop
    import time
    status = "STOPPING"
    while status not in ["TERMINATED", "STOPPED"]:
        time.sleep(5)
        instance = compute.instances().get(
            project=GCP_PROJECT,
            zone=GCP_ZONE,
            instance=GCP_INSTANCE
        ).execute()
        status = instance["status"]
        print(f"Waiting for shutdown... Status = {status}")

    await ctx.send(f"✅ Server has been successfully stopped. Status: **{status}**")

@bot.command()
async def status(ctx):
    instance = compute.instances().get(
        project=GCP_PROJECT,
        zone=GCP_ZONE,
        instance=GCP_INSTANCE
    ).execute()

    status = instance["status"]

    if status == "RUNNING":
        ip = instance["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
        await ctx.send(f"📡 Server is **{status}**\n🌐 Connect at `{ip}:8211`")
    else:
        await ctx.send(f"🛑 Server is **{status}**. It is not currently running.")

print("Commands loaded:", [cmd.name for cmd in bot.commands])
bot.run(DISCORD_TOKEN)