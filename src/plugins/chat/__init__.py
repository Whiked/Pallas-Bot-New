import asyncio
import re
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import GROUP, Bot, GroupMessageEvent
import httpx
import json
from openai import AsyncOpenAI

# 替换为你的文心key和deepseek key，文心用于简单问答，ds用于锐评（锐评好玩多了
BAIDU_API_KEY = "xxxxxxxxxx"
BAIDU_SECRET_KEY = "xxxxxxxxxx"
DEEPSEEK_API_KEY = "xxxxxxxxxx"

deepseek_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
) 

PARAS_BACKGROUND = (
    "你是来自米诺斯的祭司帕拉斯，曾作为特殊病人来到罗德岛秘密治疗。"
    "你对罗德岛充满兴趣，成为了一名作战干员。你拥有广泛的兴趣，"
    "包括医学、格斗技巧和方程式战车竞技。你在阿克罗蒂村担任祭司期间，"
    "积极参与村庄的建设和对抗萨尔贡部落的侵扰，赢得了村民的信任和尊敬。"
    "你的语气温和而坚定，充满智慧与勇气。"
)

PARAS_BACKGROUND_RUIPING = "用刻薄嘲讽的话进行锐评，语言直接一针见血，回答限100字内"

async def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_API_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, params=params)
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            logger.error(f"获取百度token失败: {e}")
            return None

async def ask_text(question: str, use_ruiping: bool = False):
    if not use_ruiping: 
        access_token = await get_access_token()
        if not access_token:
            return None
            
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_speed?access_token={access_token}"
        payload = {
            "messages": [
                {"role": "assistant", "content": PARAS_BACKGROUND},
                {"role": "user", "content": question}
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                return response.json().get('result')
        except Exception as e:
            logger.error(f"百度API错误: {e}")
            return None
    else: 
        try:
            response = await deepseek_client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": PARAS_BACKGROUND_RUIPING},
                    {"role": "user", "content": question}
                ],
                max_tokens=110,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"DeepSeek锐评失败: {str(e)}")
            return "让你爹歇歇"


ask_cmd = on_command("牛牛我问你", permission=GROUP, priority=10, block=True)
ruiping_cmd_1 = on_command("牛牛锐评一下", permission=GROUP, priority=10, block=True)
ruiping_cmd_2 = on_command("牛牛锐评", permission=GROUP, priority=10, block=True)

is_asking = False
last_ask_time = 0
cooldown = 30

@ask_cmd.handle()
async def handle_ask(bot: Bot, event: GroupMessageEvent):
    global is_asking, last_ask_time
    if time.time() - last_ask_time < cooldown:
        await bot.send(event, '等一下再问！')
        return
    
    message = event.get_message().extract_plain_text().strip()
    if match := re.match(r'牛牛我问你\s+(.+)', message):
        question = match.group(1).strip()
        if question:
            await bot.send(event, '让我仔细考虑一下')
            answer = await ask_text(question)
            await bot.send(event, answer or '连接罗德岛主脑失败...')
            last_ask_time = time.time()

@ruiping_cmd_1.handle()
@ruiping_cmd_2.handle()
async def handle_ruiping(bot: Bot, event: GroupMessageEvent):
    global is_asking, last_ask_time
    if time.time() - last_ask_time < cooldown:
        await bot.send(event, '锐评你麻辣隔壁，让你爹歇歇，你们这是要把我脑回路开发成免费景点，还指望我24小时当你们的收费导游？')
        return
    
    message = event.get_message().extract_plain_text().strip()
    if match := re.match(r'(?:牛牛锐评一下|牛牛锐评)\s+(.+)', message):
        question = match.group(1).strip()
        if question:
            await bot.send(event, '正在酝酿...')
            answer = await ask_text(question, use_ruiping=True)
            await bot.send(event, answer or '这个目标不值得锐评')
            last_ask_time = time.time()