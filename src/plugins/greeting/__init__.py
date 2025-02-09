import asyncio
from io import BytesIO
from pathlib import Path
import random
from nonebot.adapters.onebot.v11 import Bot, PokeNotifyEvent
from nonebot import on_command, on_notice
from nonebot.adapters.onebot.v11 import (
    GROUP,
    Bot,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    Message,
    MessageSegment,
    PokeNotifyEvent,
)
from nonebot.typing import T_State

# 处理群成员增加的 Matcher
increase_handler = on_notice(priority=10)

# 处理戳一戳的 Matcher
poke_handler = on_notice(priority=10)

voice_names = [
    "编入队伍", "戳一下", "干员报到", "交谈1", "交谈2", "交谈3",
    "晋升后交谈1", "晋升后交谈2", "精英化晋升1", "任命队长",
    "问候", "闲置", "信赖触摸", "信赖提升后交谈1",
    "信赖提升后交谈2", "信赖提升后交谈3"
]

# 音频文件夹路径
voice_path = Path("C:/Users/12092/Desktop/niu/NP/resource/voices/Pallas")

call_me_cmd = on_command("牛牛说话", aliases={"帕拉斯"}, permission=GROUP, priority=30, block=False)

@call_me_cmd.handle()
async def handle_call_me(bot: Bot, event: GroupMessageEvent, state: T_State):
    selected_voice = random.choice(voice_names)
    voice_file_path = voice_path / f"{selected_voice}.wav"
    print(f"Selected voice file: {voice_file_path}")
    try:
        with open(voice_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            await call_me_cmd.finish(MessageSegment.record(BytesIO(audio_bytes)))
    except Exception as e:
        print(f"Error reading audio file: {e}")

# 处理群成员增加事件
@increase_handler.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    if event.user_id == int(bot.self_id):
        text_msg = '我是来自米诺斯的祭司帕拉斯，会在罗德岛休息一段时间......虽然这么说，我渴望以美酒和戏剧被招待，更渴望走向战场。'
    else:
        text_msg = MessageSegment.at(event.user_id) + ' 博士，欢迎加入这盛大的庆典！我是来自米诺斯的祭司帕拉斯......要来一杯美酒么？'
        selected_voice = random.choice(voice_names)
        voice_file_path = voice_path / f"{selected_voice}.wav"
        try:
            with open(voice_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            await bot.send(event, MessageSegment.record(BytesIO(audio_bytes)))
        except Exception as e:
            print(f"Error reading audio file: {e}")

    await bot.send(event, text_msg)

# 处理戳一戳事件 注 暂时无法戳
@poke_handler.handle()
async def handle_poke(bot: Bot, event: PokeNotifyEvent):
    # 确认戳的目标是当前 Bot
    if event.target_id == int(bot.self_id):
        delay = random.randint(1, 3)
        await asyncio.sleep(delay)
        try:
            # 使用 send_group_poke 来戳回用户
            await bot.call_api("send_group_poke", group_id=event.group_id, user_id=event.user_id)
            print(f"Successfully poked back user_id: {event.user_id} in group_id: {event.group_id}")
        except Exception as e:
            print(f"Error sending poke: {e}")