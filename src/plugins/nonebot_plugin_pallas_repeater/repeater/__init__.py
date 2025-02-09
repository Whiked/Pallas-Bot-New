import asyncio
import random
import re
import threading
import time
import os
import ssl
import aiohttp
import hashlib
import base64
import glob
from typing import Optional
from datetime import datetime

from nonebot import on_message, on_notice, require, get_bot, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, GroupRecallNoticeEvent
from nonebot.adapters.onebot.v11 import permission, Message, MessageSegment
from nonebot.exception import ActionFailed
from nonebot.permission import Permission
from nonebot.permission import SUPERUSER
from nonebot.rule import keyword, to_me, Rule
from nonebot.typing import T_State

from .model import Chat
from ..config import BotConfig
from ..utils.array2cqcode import try_convert_to_cqcode
from ..utils.media_cache import insert_image, get_image

#请自行设置一个目录，将用于bot缓存部分表情包文件
IMAGE_CACHE_DIR = r"xxxxxx"

any_msg = on_message(
    priority=15,
    block=False,
    permission=permission.GROUP  # | permission.PRIVATE_FRIEND
)


async def is_shutup(self_id: int, group_id: int) -> bool:
    info = await get_bot(str(self_id)).call_api('get_group_member_info', **{
        'user_id': self_id,
        'group_id': group_id
    })
    flag: bool = info['shut_up_timestamp'] > time.time()

    logger.info('bot [{}] in group [{}] is shutup: {}'.format(
        self_id, group_id, flag))

    return flag


message_id_lock = threading.Lock()
message_id_dict = {}

async def download_and_cache_image(url: str) -> Optional[str]:
    md5_str = hashlib.md5(url.encode("utf-8")).hexdigest()
    year_month_pattern = re.compile(r'^\d{4}-\d{2}$')

    existing_file = None
    for dir_name in os.listdir(IMAGE_CACHE_DIR):
        if not year_month_pattern.match(dir_name):
            continue
        
        dir_path = os.path.join(IMAGE_CACHE_DIR, dir_name)
        if os.path.isdir(dir_path):
            pattern = os.path.join(dir_path, md5_str + ".*")
            matches = glob.glob(pattern)
            if matches:
                existing_file = matches[0]
                break

    if existing_file:
        try:
            with open(existing_file, "rb") as f:
                content = f.read()
            return "base64://" + base64.b64encode(content).decode()
        except Exception as e:
            logger.warning(f"读取缓存失败 {existing_file}: {e}")

    today = datetime.now()
    year_month_str = f"{today.year:04d}-{today.month:02d}"
    cache_folder = os.path.join(IMAGE_CACHE_DIR, year_month_str)
    os.makedirs(cache_folder, exist_ok=True)

    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        ssl_ctx.set_ciphers('DEFAULT@SECLEVEL=1')

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_ctx)
        ) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"下载失败 HTTP {resp.status}")
                    return None

                content = await resp.read()
                content_type = resp.headers.get("Content-Type", "").lower()
                ext = ".jpg"
                if "png" in content_type:
                    ext = ".png"
                elif "gif" in content_type:
                    ext = ".gif"

                filename = md5_str + ext
                save_path = os.path.join(cache_folder, filename)
                with open(save_path, "wb") as f:
                    f.write(content)

                return "base64://" + base64.b64encode(content).decode()

    except Exception as e:
        logger.warning(f"下载异常: {e}")
        return None

async def post_proc(message: Message, self_id: int, group_id: int) -> Message:
    new_msg = Message()
    for seg in message:
        #过滤poke，保证无poke传出
        if seg.type == 'text':
            if "[CQ:poke," in seg.data['text']:
                logger.info(f"Found poke in text segment, filtering out: {seg}")
                continue

        if seg.type == 'at':
            try:
                info = await get_bot(str(self_id)).call_api('get_group_member_info', **{
                    'user_id': seg.data['qq'],
                    'group_id': group_id
                })
            except ActionFailed:  # 群员不存在
                continue
            nick_name = info['card'] if info['card'] else info['nickname']
            #new_msg += '@{}'.format(nick_name) 这是假艾特，可自行设置，把下面那行的真艾特注释掉再把这行前面的注释删了即可
            new_msg += MessageSegment.at(seg.data['qq'])
        elif seg.type == 'image':
            cq_code = str(seg)
            base64_data = get_image(cq_code)
            if base64_data:
                new_msg += MessageSegment.image(file=base64_data)
            else:
                file_url = seg.data.get("file", "")
                if file_url.startswith("http"):
                    logger.info(f"检测到外链图片：{file_url}，准备下载并缓存。")
                    base64_data = await download_and_cache_image(file_url)
                    if base64_data:
                        new_msg += MessageSegment.image(file=base64_data)
                    else:
                        logger.warning(f"外链图片下载失败/无效，跳过发送：{file_url}")
                else:
                    new_msg += seg

        else:
            new_msg += seg

    # 回调或其他后置逻辑
    if not Chat.reply_post_proc(str(message), str(new_msg), self_id, group_id):
        logger.warning('bot [{}] post_proc failed in group [{}]: [{}] -> [{}]'.format(
            self_id, group_id, str(message)[:30], str(new_msg)[:30]))

    if len(new_msg) == 0:
        return None
        
    return new_msg


@any_msg.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    to_learn = True
    # 多账号登陆，且在同一群中时；避免一条消息被处理多次
    with message_id_lock:
        message_id = event.message_id
        group_id = event.group_id
        if group_id in message_id_dict:
            if message_id in message_id_dict[group_id]:
                to_learn = False
        else:
            message_id_dict[group_id] = []

        group_message = message_id_dict[group_id]
        group_message.append(message_id)
        if len(group_message) > 100:
            group_message = group_message[:-10]

    chat: Chat = Chat(event)

    answers = None
    config = BotConfig(event.self_id, event.group_id)
    if config.is_cooldown('repeat'):
        answers = chat.answer()

    if to_learn:
        for seg in event.message:
            if seg.type == "image":
                await insert_image(seg)

        chat.learn()

    if not answers:
        return

    config.refresh_cooldown('repeat')
    delay = random.randint(2, 5)
    for item in answers:
        msg = await post_proc(item, event.self_id, event.group_id)
        logger.info(
            'bot [{}] ready to send [{}] to group [{}]'.format(event.self_id, str(msg)[:30], event.group_id))

        await asyncio.sleep(delay)
        config.refresh_cooldown('repeat')
        try:
            await any_msg.send(msg)
        except ActionFailed:
            if not BotConfig(event.self_id).security():
                continue

            # 自动删除失效消息。若 bot 处于风控期，请勿开启该功能
            shutup = await is_shutup(event.self_id, event.group_id)
            if not shutup:  # 说明这条消息失效了
                logger.info('bot [{}] ready to ban [{}] in group [{}]'.format(
                    event.self_id, str(item), event.group_id))
                Chat.ban(event.group_id, event.self_id,
                         str(item), 'ActionFailed')
                break
        delay = random.randint(1, 3)


async def is_config_admin(event: GroupMessageEvent) -> bool:
    return BotConfig(event.self_id).is_admin_of_bot(event.user_id)


IsAdmin = permission.GROUP_OWNER | permission.GROUP_ADMIN | SUPERUSER | Permission(
    is_config_admin)


async def is_reply(bot: Bot, event: GroupMessageEvent, state: T_State) -> bool:
    return bool(event.reply)


ban_msg = on_message(
    rule=to_me() & keyword('不可以') & Rule(is_reply),
    priority=5,
    block=True,
    permission=IsAdmin
)


@ban_msg.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    if '[CQ:reply,' not in try_convert_to_cqcode(event.raw_message):
        return False

    raw_message = ''
    for item in event.reply.message:
        raw_reply = str(item)
        # 去掉图片消息中的 url, subType 等字段
        raw_message += re.sub(r'(\[CQ\:.+)(?:,url=*)(\])',
                              r'\1\2', raw_reply)

    logger.info('bot [{}] ready to ban [{}] in group [{}]'.format(
        event.self_id, raw_message, event.group_id))

    try:
        await bot.delete_msg(message_id=event.reply.message_id)
    except ActionFailed:
        logger.warning(
            'bot [{}] failed to delete [{}] in group [{}]'.format(
                event.self_id,
                raw_message, event.group_id))

    if Chat.ban(event.group_id, event.self_id, raw_message, str(event.user_id)):
        await ban_msg.finish('这对角可能会不小心撞倒些家具，我会尽量小心。')


async def is_admin_recall_self_msg(bot: Bot, event: GroupRecallNoticeEvent):
    # 好像不需要这句
    # if event.notice_type != "group_recall":
    #     return False
    self_id = event.self_id
    user_id = event.user_id
    group_id = event.group_id
    operator_id = event.operator_id
    if self_id != user_id:
        return False
    # 如果是自己撤回的就不用管
    if operator_id == self_id:
        return False
    operator_info = await bot.get_group_member_info(
        group_id=group_id, user_id=operator_id
    )
    return operator_info['role'] == 'owner' or operator_info['role'] == 'admin'


ban_recalled_msg = on_notice(
    rule=Rule(is_admin_recall_self_msg),
    priority=5,
    block=True
)


@ban_recalled_msg.handle()
async def _(bot: Bot, event: GroupRecallNoticeEvent, state: T_State):
    try:
        msg = await bot.get_msg(message_id=event.message_id)
    except ActionFailed:
        logger.warning(
            'bot [{}] failed to get msg [{}]'.format(
                event.self_id,
                event.message_id))
        return

    raw_message = ''
    # 使用get_msg得到的消息不是消息序列，使用正则生成一个迭代对象
    for item in re.compile(r'\[[^\]]*\]|\w+').findall(try_convert_to_cqcode(msg['message'])):
        raw_reply = str(item)
        # 去掉图片消息中的 url, subType 等字段
        raw_message += re.sub(r'(\[CQ\:.+)(?:,url=*)(\])',
                              r'\1\2', raw_reply)

    logger.info('bot [{}] ready to ban [{}] in group [{}]'.format(
        event.self_id, raw_message, event.group_id))

    if Chat.ban(event.group_id, event.self_id, raw_message, str(f'recall by {event.operator_id}')):
        await ban_recalled_msg.finish('这对角可能会不小心撞倒些家具，我会尽量小心。')


async def message_is_ban(bot: Bot, event: GroupMessageEvent, state: T_State) -> bool:
    return event.get_plaintext().strip() == '不可以发这个'


ban_msg_latest = on_message(
    rule=to_me() & Rule(message_is_ban),
    priority=5,
    block=True,
    permission=IsAdmin
)


@ban_msg_latest.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    logger.info(
        'bot [{}] ready to ban latest reply in group [{}]'.format(
            event.self_id, event.group_id))

    try:
        await bot.delete_msg(message_id=event.reply.message_id)
    except ActionFailed:
        logger.warning(
            'bot [{}] failed to delete latest reply [{}] in group [{}]'.format(
                event.self_id, event.raw_message,
                event.group_id))

    if Chat.ban(event.group_id, event.self_id, '', str(event.user_id)):
        await ban_msg_latest.finish('这对角可能会不小心撞倒些家具，我会尽量小心。')


speak_sched = require('nonebot_plugin_apscheduler').scheduler


@speak_sched.scheduled_job('interval', seconds=60)
async def speak_up():
    """
    间隔 60 秒执行一次主动发言逻辑。
    """
    ret = Chat.speak()
    if not ret:
        return

    bot_id, group_id, messages = ret

    for msg in messages:
        if "[CQ:poke," in str(msg):
            logger.warning(f"Skipping poke message in speak_up: {msg}")
            continue

        # 调用 post_proc，把其中可能含有的外链图片转成本地缓存/BASE64
        processed_msg = await post_proc(msg, bot_id, group_id)
        if not processed_msg:
            continue

        logger.info(
            f'bot [{bot_id}] ready to speak after post_proc: [{processed_msg}] to group [{group_id}]'
        )

        await get_bot(str(bot_id)).call_api('send_group_msg', **{
            'message': processed_msg,
            'group_id': group_id
        })

        await asyncio.sleep(random.randint(2, 5))



update_sched = require('nonebot_plugin_apscheduler').scheduler


@update_sched.scheduled_job('cron', hour='4')
def update_data():
    Chat.sync()
    Chat.clearup_context()
