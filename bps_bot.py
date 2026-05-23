import discord
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# ============================================================
# PASTE YOUR BOT TOKEN HERE (the new one you reset)
TOKEN = "YOUR_BOT_TOKEN_HERE"

# The Discord channel name to post circulars in
CHANNEL_NAME = "general"

# How often to check for new circulars (in seconds)
# 1800 = 30 minutes
CHECK_INTERVAL = 1800
# ============================================================

CIRCULAR_URL = "https://www.bpsdoha.net/circular"
SEEN_FILE = "seen_circulars.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

async def get_circulars():
    async with aiohttp.ClientSession() as session:
        async with session.get(CIRCULAR_URL) as resp:
            html = await resp.text()
    
    soup = BeautifulSoup(html, "html.parser")
    circulars = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)
        # Filter for circular category links
        if "/circular/category/" in href and text:
            full_url = href if href.startswith("http") else "https://www.bpsdoha.net" + href
            circulars.append((text, full_url))

    return circulars

class BPSBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.seen = load_seen()
        self.start_date = datetime.now().date()

    async def on_ready(self):
        print(f"Bot is online as {self.user}")
        self.loop.create_task(self.check_circulars())

    async def check_circulars(self):
        await self.wait_until_ready()
        channel = discord.utils.get(self.get_all_channels(), name=CHANNEL_NAME)

        if not channel:
            print(f"Could not find channel: {CHANNEL_NAME}")
            return

        while not self.is_closed():
            try:
                circulars = await get_circulars()
                new_ones = []

                for (title, url) in circulars:
                    if url not in self.seen:
                        self.seen.add(url)
                        new_ones.append((title, url))

                if new_ones:
                    save_seen(self.seen)
                    for (title, url) in new_ones:
                        embed = discord.Embed(
                            title=f"📢 New BPS Circular",
                            description=f"**{title}**\n\n[Click here to view circulars]({url})",
                            color=0x1E90FF,
                            timestamp=datetime.now()
                        )
                        embed.set_footer(text="Birla Public School, Doha")
                        await channel.send(embed=embed)

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked. {len(new_ones)} new circular(s) found.")

            except Exception as e:
                print(f"Error: {e}")

            await asyncio.sleep(CHECK_INTERVAL)

client = BPSBot()
client.run(TOKEN)
