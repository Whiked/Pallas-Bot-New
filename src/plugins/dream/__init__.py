import asyncio
import random
import re
import time
import json
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import GROUP, Bot, GroupMessageEvent
import httpx

# 替换为你的文心 API Key 和 Secret Key
API_KEY = "xxxxxxxxxx"
SECRET_KEY = "xxxxxxxxxx"


async def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Access token response: {data}")
            return data.get("access_token")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting access token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while getting access token: {e}")
            return None

async def gen_text(text: str):
    """
    调用文心一言 ERNIE-Speed-8K 模型生成文本
    :param text: 用户输入的提示语
    :return: 分段后的生成文本，或是None(如果失败)
    """
    access_token = await get_access_token()
    if not access_token:
        logger.error("无法获取 access token")
        return None

    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_speed?access_token={access_token}"
    payload = {
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Gen text response: {data}")
            if 'result' in data:
                split_result = data['result'].split('：', 1)
                result = split_result[1] if len(split_result) > 1 else split_result[0]

                segments = re.split(r'[。？！\n]', result)
                segments = [seg.strip() for seg in segments if seg.strip()]
                return segments
            else:
                logger.error("API 请求失败，响应中不包含 'result'")
                logger.error(f"完整响应内容: {data}")
                return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during gen_text: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during gen_text: {e}")
            return None

dream_cmd = on_command("牛牛做梦", permission=GROUP, priority=13, block=False)

is_dreaming = False
last_dream_time = 0
cooldown = 30  # 冷却时间，单位：秒

@dream_cmd.handle()
async def dream(bot: Bot, event: GroupMessageEvent):
    global is_dreaming, last_dream_time

    current_time = time.time()
    if current_time - last_dream_time < cooldown:
        await bot.send(event, '时光飞逝，梦境短暂。稍等片刻，我还在编织你的梦……')
        return 

    is_dreaming = True

    try:
        prompts = [
    "写一个70到100字的奇妙小故事，内容离奇搞笑，充满意想不到的转折和荒诞元素，让人捧腹大笑又感到惊讶。",
    "作为一名古怪的美食博主，写一篇100字的美食评价。选择一种奇特或虚构的食物，加入疯狂的描述和幽默的点评，让人忍俊不禁。",
    "编写一个70到100字的奇幻爱情故事，描述两个完全不同物种的爱情，剧情充满幽默和荒诞的转折，结局出人意料且让人会心一笑。",
    "写一篇130到180字的小红书风格探店文案，描述一家奇特或虚构的店铺，内容充满幽默和荒诞的细节，让读者捧腹大笑的同时产生浓厚兴趣。",
    "提供一个100字左右的幽默建议，关于第一次拜访女朋友父母时可以送什么奇特又搞笑的礼物，既能逗笑对方又能留下深刻印象。",
    "给出一个100字左右的搞笑建议，针对母胎单身26年的奇葩人士如何找到对象，内容充满幽默感和意想不到的创意。",
    "编写一个80到120字的奇幻冒险故事，主角是一只会说话的西瓜，充满幽默和荒诞的情节，让人忍不住大笑。",
    "描述一个普通人一天中发生的离奇搞笑事件，字数在70到100字之间，充满奇妙的幽默感和意外的转折。",
    "创造一个荒诞有趣的发明，并用100字左右描述其功能和使用场景，内容充满幽默和奇思妙想。",
    "写一个90字左右的对话场景，描述两只性格迥异的动物之间的搞笑互动，充满幽默和奇妙的情节。",
    "描述一个70到100字的奇妙梦境场景，充满荒诞和幽默的元素，让人感到既滑稽又不可思议。",
    "编写一个80字左右的小故事，前半部分看似正常，后半部分却出现出人意料的搞笑反转，充满奇妙的幽默感。",
    "写一个100字左右的虚构产品广告，产品奇特且功能荒诞，广告内容充满幽默和夸张的描述。",
    "描述一个90字左右的超现实对话场景，人物对话内容荒诞有趣，充满奇妙的幽默感。",
    "提供一个70字左右的奇怪但幽默的建议，针对日常生活中的一个小问题，内容充满荒诞和笑点。",
    "撰写一个80字左右的荒诞新闻报道，内容虚构且充满幽默，仿佛发生在奇幻世界中的真实事件。"
]

        chosen_prompt = random.choice(prompts)

        await bot.send(event, 'Zzz...')

        text_segments = await gen_text(chosen_prompt)
        if not text_segments:
            await bot.send(event, '生成失败，请稍后再试。')
            return

        for segment in text_segments:
            await asyncio.sleep(len(segment) / 10)  # 根据文本长度动态调整延时
            await bot.send(event, segment)

        await bot.send(event, 'Zzz......')
        await bot.send(event, '......')
    finally:
        is_dreaming = False
        last_dream_time = time.time()