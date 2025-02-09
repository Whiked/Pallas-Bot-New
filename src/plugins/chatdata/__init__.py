# File: plugins/chat_recorder.py
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent

# 配置项
SAVE_ROOT = Path(r"D:\NIUcache\message")  # 存储根目录
MAX_CONTEXT = 5  # 上下文保留条数
BUFFER: Dict[str, List[str]] = {}  # 群组上下文缓冲区

# 创建存储目录（如果不存在）
SAVE_ROOT.mkdir(parents=True, exist_ok=True)

def format_context(group_id: str) -> List[str]:
    """获取并维护上下文缓冲区"""
    if group_id not in BUFFER:
        BUFFER[group_id] = []
    return BUFFER[group_id][-MAX_CONTEXT:]

def save_message(event: GroupMessageEvent):
    """消息存储核心逻辑"""
    # 构建数据记录
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "group_id": str(event.group_id),
        "user_id": str(event.user_id),
        "message": event.get_message().extract_plain_text().strip(),
        "context": format_context(str(event.group_id)),
        "message_id": str(event.message_id)
    }

    # 更新上下文
    BUFFER[str(event.group_id)].append(
        f"{record['user_id']}: {record['message']}"
    )
    if len(BUFFER[str(event.group_id)]) > MAX_CONTEXT * 2:
        BUFFER[str(event.group_id)] = BUFFER[str(event.group_id)][-MAX_CONTEXT:]

    # 按群号/日期存储
    save_dir = SAVE_ROOT / str(event.group_id)
    save_dir.mkdir(exist_ok=True)
    
    filename = datetime.now().strftime("%Y%m%d") + ".jsonl"
    with open(save_dir / filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# 创建消息处理器
recorder = on_message(priority=999, block=False)

@recorder.handle()
async def record_handler(event: GroupMessageEvent):
    if not hasattr(event, "group_id"):
        return
    
    # 初始化群组缓冲区
    if str(event.group_id) not in BUFFER:
        BUFFER[str(event.group_id)] = []
    
    # 执行存储
    try:
        save_message(event)
    except Exception as e:
        print(f"记录消息失败：{str(e)}")