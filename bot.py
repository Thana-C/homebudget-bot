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
    parts = [p.strip() for p in text.split(',')]
    for part in parts:
        match = re.match(r'^(.+?)\s+(\d+(?:\.\d+)?)$', part.strip())
        if match:
            desc = match.group(1).strip()
            amount = float(match.group(2))
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
        await message.reply('❌ รูปแบบไม่ถูก ลองใหม่นะครับ เช่น: `ค่าส่งอง 80, ข้าวเช้า 80, กาแฟ 100`')
        return

    added = []
    for desc, amount in items:
        ws.append_row([today, desc, amount, '', person, 'expense'])
        added.append(f'• {desc} = ฿{int(amount):,}')

    total = sum(a for _, a in items)
    reply = '✅ บันทึกแล้วครับ\n' + '\n'.join(added) + f'\n\n💰 รวม: ฿{int(total):,}'
    await message.reply(reply)

client.run(DISCORD_TOKEN)
