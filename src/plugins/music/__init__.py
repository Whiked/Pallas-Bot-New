from io import BytesIO
from nonebot import on_command, on_message, logger
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import GROUP, MessageSegment
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
import random
import os

def get_music_name():
    resource_path = "resource/music/"
    all_music = os.listdir(resource_path)
    if not all_music:
        logger.warning("No music files found in the directory.")
        return None
    music = random.choice(all_music)
    music_path = resource_path + music
    logger.info(f"Selected music file: {music_path}")
    return music_path

music_cmd = on_command("牛牛唱歌", aliases={"欢乐水牛"}, permission=GROUP, priority=13, block=False)

@music_cmd.handle()
async def _(bot: Bot, event: Event, state: T_State):
    music_file_path = get_music_name()
    if not music_file_path or not os.path.exists(music_file_path):
        logger.error(f"Music file not found: {music_file_path}")
        return
    try:
        with open(music_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            await bot.send(event, MessageSegment.record(BytesIO(audio_bytes)))
            logger.info("Music message sent.")
    except Exception as e:
        logger.error(f"Error reading audio file: {e}")