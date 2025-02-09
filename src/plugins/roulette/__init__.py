from datetime import datetime
import random
import time

from nonebot import on_command, require
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.typing import T_State
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_pallas_repeater.drink import BotConfig

# 引入日志记录
import logging
logger = logging.getLogger(__name__)

# 全局状态字典
roulette_status = {}
roulette_count = {}
roulette_player = {}
roulette_time = {}
group_status = {}

# 轮盘命令处理器
roulette_msg = on_command('牛牛轮盘', permission=GROUP, priority=5, block=True)

@roulette_msg.handle()
async def handle_roulette(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id

    # 检查轮盘是否已经开始
    if roulette_status.get(group_id, False):
        await roulette_msg.finish("轮盘已经开始了！")
        return

    # 使用 BotConfig 检查是否在睡眠状态
    config = BotConfig(event.self_id, group_id)
    if config.is_sleep():
        await roulette_msg.finish("Zzz...")
        return

    # 检查是否醉酒
    is_drunk = config.drunkenness() > 0

    # 初始化轮盘状态
    roulette_status[group_id] = True
    roulette_count[group_id] = 0
    roulette_player[group_id] = []
    roulette_time[group_id] = time.time()

    # 发送轮盘开始的消息，根据醉酒状态调整消息内容
    if is_drunk:
        await roulette_msg.send(
            "这是一把充满荣耀与死亡的左轮手枪，六个弹槽有多颗子弹，"
            "中弹的那个人将会被禁言1-20分钟。勇敢的战士们啊，扣动你们的扳机吧！"
        )
    else:
        await roulette_msg.send(
            "这是一把充满荣耀与死亡的左轮手枪，六个弹槽只有一颗子弹，"
            "中弹的那个人将会被禁言1-20分钟。勇敢的战士们啊，扣动你们的扳机吧！"
        )

shot_msg = on_command('牛牛开枪', permission=GROUP, priority=5, block=True)

shot_text = [
    '无需退路。',
    '英雄们啊，为这最强大的信念，请站在我们这边。',
    '颤抖吧，在真正的勇敢面前。',
    '哭嚎吧，为你们不堪一击的信念。',
    '现在可没有后悔的余地了。',
    '你将在此跪拜。'
]

@shot_msg.handle()
async def handle_shot(bot: Bot, event: GroupMessageEvent, state: T_State):
    group_id = event.group_id
    user_id = event.user_id

    if not roulette_status.get(group_id, False):
        await shot_msg.finish("轮盘还没有开始！")
        return

    # 记录参与的玩家
    if user_id not in roulette_player[group_id]:
        roulette_player[group_id].append(user_id)

    # 记录开枪次数
    roulette_count[group_id] = roulette_count.get(group_id, 0) + 1
    shot_number = roulette_count[group_id]  # 第几枪

    # 使用 BotConfig 检查是否在醉酒状态
    config = BotConfig(event.self_id, group_id)
    is_drunk = config.drunkenness() > 0

    # 计算命中概率
    if shot_number == 6:
        hit_probability = 0.99  # 第六枪的命中概率为0.99
    else:
        hit_probability = 1.0 / (7 - shot_number) if (7 - shot_number) > 0 else 1.0
    hit = (random.random() < hit_probability)

    logger.info(f"Group {group_id}: User {user_id} fired shot {shot_number}. Hit: {hit}")

    if hit:
        group_info = group_status.get(group_id, {})

        if is_drunk:
            players_to_ban = min(len(roulette_player[group_id]), 3)
            banned_anyone = False
            for i in range(players_to_ban):
                user_id_to_ban = (
                    roulette_player[group_id].pop(0)
                    if roulette_player[group_id] else user_id
                )

                info = await bot.call_api(
                    'get_group_member_info',
                    group_id=group_id,
                    user_id=user_id_to_ban
                )
                if info.get('role') in ['admin', 'owner']:
                    await shot_msg.send(
                        '听啊，悲鸣停止了。这是幸福的和平到来前的宁静。'
                    )
                    # 重置相关状态
                    roulette_status.pop(group_id, None)
                    roulette_count.pop(group_id, None)
                    roulette_player.pop(group_id, None)
                    return

                durat = random.randint(60, 1200)
                await bot.call_api(
                    'set_group_ban',
                    group_id=group_id,
                    user_id=user_id_to_ban,
                    duration=durat
                )
                reply_msg = (
                    MessageSegment.text("米诺斯英雄们的故事......有喜剧，便也会有悲剧。舍弃了荣耀，")
                    + MessageSegment.at(user_id_to_ban)
                    + MessageSegment.text(f"({i+1}/3) 选择回归平凡......")
                )
                await shot_msg.send(reply_msg)
                banned_anyone = True

            roulette_status.pop(group_id, None)
            roulette_count.pop(group_id, None)
            roulette_player.pop(group_id, None)

            if not banned_anyone:
                await shot_msg.send("")
            return

        else:
            info = await bot.call_api(
                'get_group_member_info',
                group_id=group_id,
                user_id=user_id
            )
            if info.get('role') in ['admin', 'owner']:
                await shot_msg.send(
                    '听啊，悲鸣停止了。这是幸福的和平到来前的宁静。'
                )
                roulette_status.pop(group_id, None)
                roulette_count.pop(group_id, None)
                roulette_player.pop(group_id, None)
                return

            durat = random.randint(60, 1200)
            await bot.call_api(
                'set_group_ban',
                group_id=group_id,
                user_id=user_id,
                duration=durat
            )
            reply_msg = (
                MessageSegment.text("米诺斯英雄们的故事......有喜剧，便也会有悲剧。舍弃了荣耀，")
                + MessageSegment.at(user_id)
                + MessageSegment.text(" 选择回归平凡......")
            )
            roulette_status.pop(group_id, None)
            roulette_count.pop(group_id, None)
            roulette_player.pop(group_id, None)
            await shot_msg.finish(reply_msg)
            return

    else:
        if shot_number == 6:
            await shot_msg.send(
                "我的手中的这把武器，找了无数工匠都难以修缮如新。"
                "不......不该如此......"
            )
            roulette_status.pop(group_id, None)
            roulette_count.pop(group_id, None)
            roulette_player.pop(group_id, None)
            return
        else:
            if shot_number <= len(shot_text):
                reply_msg = f"{shot_text[shot_number - 1]} ( {shot_number} / 6 )"
            else:
                # 设置一个默认消息，防止未赋值
                reply_msg = "轮盘已经结束力"
                roulette_status.pop(group_id, None)
                roulette_player.pop(group_id, None)
                roulette_count.pop(group_id, None)
            await shot_msg.send(reply_msg)


@scheduler.scheduled_job('cron', hour='3')
async def update_data():
    for group in group_status:
        group_status[group]['next_drink_time'] = datetime.min
        group_status[group]['sober_up_time'] = datetime.min
        group_status[group]['is_sleeping'] = False