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

CATEGORIES = {
    'Breakfast':        ['ข้าวเช้า','โจ๊ก','ขนมปัง','แซนวิช','แซนวิส','โอวัลติน'],
    'Lunch':            ['ข้าวเที่ยง','ข้าวเทียง','ก๋วยเตี๋ยว','ราดหน้า','ผัดไทย','กินข้าวเที่ยง'],
    'Dinner':           ['ข้าวเย็น','ข้าวเยน','ข้าบเย็น','ข้าววเย็น','กับข้าวเย็น','กับข้าวเยน','ข้าวให้','กินข้าวกีบ','ข้าว'],
    'Coffee/Tea':       ['กาแฟ','กรแฟ','ชา','นมสด','มัทฉะ','ชานม','น้ำชา','น้ำปั่น','ไอศครีม'],
    'Snack':            ['ขนม','ของกินเล่น','กินเล่น','ลูกชิ้น','ลูกชิัน','กล้วยทอด','snack','ผลไม้','ขนมหวาน'],
    'Stuff':            ['เซเว่น','7-11','maxvalue','ร้านสะดวกซื้อ','ซื้อจ้าว'],
    'Transport':        ['จอดรถ','เดินทาง','ทางด่วน','ค่าส่ง','ส่งของ','ค่าส่งของ','พัสดุ','เติมน้ำมัน','น้ำมัน','easypass','ด่วน'],
    'น้ำท่อม':          ['น้ำท่อม','ยาน้ำท่อม','น้ำเปล่า','น้ำ'],
    'Shopping':         ['ช้อปปิ้ง','เสื้อผ้า','ของใช้','ซ่อม','ซ่อมรองเท้า','ตัดผม','ล้างรถ','ซักผ้า','หัวพอด','พอด','shopee','lazada','amazon'],
    'Beer':             ['เบียร์','beer','เหล้า','สุรา'],
    'Drug+Cigarette':   ['บุหรี่','ยา','iqos','บุฟรี่ไฟฟ้า','ยาสูบ'],
    'Cat':              ['อาหารแมว','แมวหาหมอ','ของแมว','แมว'],
    'ทำบุญ':            ['ทำบุญ','ใส่ซอง','งานแต่ง','ซองงานแต่ง','ปล่อยปลา'],
    'ลงทุน':            ['ลงทุน'],
    'Travel':           ['เที่ยว','travel','esim'],
    'Income':           ['เงินเดือน','ค่าเช่า','รายได้','โบนัส','เงินพิเศษ'],
    'Fixed/คอนโด':      ['คอนโด','ค่าเช่าคอนโด','ค่าห้อง'],
    'Fixed/รถ':         ['ค่ารถ','ค่าผ่อนรถ','bmw','ค่าประกันรถ','ประกันรถ','ผ่อนรถ'],
    'Fixed/บัตรเครดิต': ['บัตรเครดิต','บัตร scb','บัตร kbank','creditcard'],
    'Fixed/อื่นๆ':      ['ค่าเน็ต','เน็ต','ค่าโทร','ประกัน','ค่าไฟ','ค่าน้ำ'],
    'โอนเงิน':          ['พี่นิ่ม','พี่ฟ้าง','พี่พอช','ให้พ่อ','คืนยาย','อั้ม','โอน','คืนเงิน'],
    'Other':            [],
}
}

PEOPLE_KEYS = []

def categorize(desc):
    d = desc.lower().strip()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in d:
                return cat
    for kw in PEOPLE_KEYS:
        if kw in desc:
            return 'Other/Lifestyle'
    return 'Other'

def parse_items(text):
    items = []
    for line in [l.strip() for l in text.strip().splitlines()]:
        if not line:
            continue
        is_income = line.startswith('+')
        clean = line.lstrip('+').strip()
        match = re.match(r'^(.+?)\s*(\d+(?:\.\d+)?)\s*$', clean)
        if match:
            desc = match.group(1).strip().rstrip('-,')
            amount = float(match.group(2))
            if desc and amount > 0:
                items.append((desc, amount, is_income))
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
        await message.reply('❌ ไม่เจอรายการ ลองใหม่นะครับ\nเช่น:\n```\nกาแฟ 80\nข้าวเที่ยง 60\n+เงินเดือน 75000```')
        return

    added = []
    total_exp = 0
    total_inc = 0

    for desc, amount, is_income in items:
        tx_type = 'income' if is_income else 'expense'
        cat = categorize(desc)
        ws.append_row([today, desc, amount, cat, person, tx_type])
        icon = '📈' if is_income else '📉'
        added.append(f'{icon} `{desc}` ฿{int(amount):,} — _{cat}_')
        if is_income:
            total_inc += amount
        else:
            total_exp += amount

    lines_out = '\n'.join(added)
    summary = []
    if total_exp > 0:
        summary.append(f'📉 จ่าย **฿{int(total_exp):,}**')
    if total_inc > 0:
        summary.append(f'📈 รับ **฿{int(total_inc):,}**')

    reply = f'✅ บันทึก {len(items)} รายการ\n{lines_out}\n\n' + ' · '.join(summary)
    await message.reply(reply)

client.run(DISCORD_TOKEN)
