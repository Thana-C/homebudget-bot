import discord
import gspread
import os
import re
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

SCOPES = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds_json = os.environ.get('GOOGLE_CREDENTIALS')
creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_ID = os.environ.get('SHEET_ID')
sh = gc.open_by_key(SHEET_ID)
ws = sh.sheet1

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_NAME = 'expenses'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def parse_items(text):
    items = []
    lines = [l.strip() for l in text.strip().splitlines()]
    for line in lines:
        if not line:
            continue
        match = re.match(r'^(.+?)\s*(\d+(?:\.\d+)?)\s*$', line)
        if match:
            desc = match.group(1).strip().rstrip('+-,')
            amount = float(match.group(2))
            if desc and amount > 0:
                items.append((desc, amount))
    return items

@client.event
async def on_ready():
    print(f'Bot ready: {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.name != CHANNEL_NAME:
        return

    text = message.content.strip()
    person = message.author.display_name
    today = datetime.now().strftime('%Y-%m-%d')

    if text.startswith('!'):
        return

    items = parse_items(text)
    if not items:
        await message.reply('❌ ไม่เจอรายการ ลองใหม่นะครับ\nเช่น:\n```\nกาแฟ 80\nข้าวเที่ยง 60\nน้ำท่อม 50```')
        return

    added = []
    total = 0
    for desc, amount in items:
        ws.append_row([today, desc, amount, '', person, 'expense'])
        added.append(f'`{desc}` ฿{int(amount):,}')
        total += amount

    lines_out = '\n'.join(added)
    reply = f'✅ บันทึก {len(items)} รายการ\n{lines_out}\n\n💰 รวม **฿{int(total):,}**'
    await message.reply(reply)

client.run(DISCORD_TOKEN)
