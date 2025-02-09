<div align="center">
  <img alt="LOGO" src="https://user-images.githubusercontent.com/18511905/195892994-c1a231ec-147a-4f98-ba75-137d89578247.png" width="360" height="270"/>
  
  ###### 图片来自于 [Pallas-Bot](https://github.com/MistEO/Pallas-Bot)
</div>

# Pallas-Bot Repeater Plugin

[![NoneBot](https://img.shields.io/badge/NoneBot-2.0.0rc3-green.svg)](https://github.com/nonebot/nonebot2)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

> 从PallasBot中独立出的插件

## ✨ 项目特色
- 跨群聊学习与自适应发言
- 轮盘、唱歌、AI对话等功能

## 📦 安装指南

### 前置需求
- Python 3.8+
- MongoDB数据库
- [NoneBot2](https://nonebot.dev/) 机器人框架
- 推荐安装 `jieba-fast` 加速分词

### 快速部署
您需要先创建一个自己的nonebot2机器人，这非常简单！可以参考下面的文档：[NoneBot2](https://nonebot.dev/docs/quick-start) <br>

建议选择simple模板，适配器建议选择FastAPI以及HTTPX，方便后续添加其他插件可以正常使用。或者使用项目内的bot.py，里面自定义了一个httpx适配器。驱动器选择onebotv11启动器。<br>

在进行一些基本bot设置后，你就可以在bot目录下手动拖入项目内的resource和src文件夹了，此时启动bot就可以自动加载这些插件。你也可以浏览nonebot插件商店来自由的安装你喜欢的插件。<br>


## 🔧 配置说明
如果您想要牛牛偷群u的id，那么请在对应目录下，修改期望概率，这是可选的，其他api key或者缓存目录设置则是必须的。<br>
如果您暂时没有两家的api key，又确实不需要`牛牛做梦`、`牛牛我问你`以及`牛牛锐评`功能，那么可以在`src\plugins\`目录下手动移除`chat`以及`dream`文件夹，这不会影响其他功能的使用。<br>
##### 括弧建议加上这几个功能，还是挺好玩的（<br>
音频文件也是可选添加的，不添加仅仅只会导致牛牛唱歌功能没有东西发出来而已。<br>

### API密钥配置
在`src\plugins\chat`目录下，修改代码添加您自己的文心key和deepseek key。<br>
在`src\plugins\dream`目录下，修改代码添加您自己的文心key。

### 功能参数调整
| 配置文件路径 | 功能说明 |
|--------------|----------|
| `src/plugins/nonebot_plugin_pallas_repeater/take_name/` | 名片夺取概率 |
| `src/plugins/nonebot_plugin_pallas_repeater/repeater/` | 图片缓存目录 |
| `resource/music/` | 自定义音频文件 |

## 🎮 功能列表

### 牛牛有什么功能？

牛牛的功能就是废话和复读。牛牛几乎所有的发言都是从群聊记录中学习而来的，并非作者硬编码写入的。群友们平时怎么聊，牛牛就会怎么回，可以认为是高级版的复读机

### 那为什么牛牛说了一些群里从来没说过的话？

牛牛有跨群功能，若超过 N 个群都有类似的发言，就会作为全局发言，在任何群都生效

### 你说牛牛没有功能，为什么有时候查询信息、或者一些其它指令，牛牛会回复？

从别的机器人（可能是其他群）那里学来的

~~你这机器人功能不错呀，现在牛牛也会了！~~

### 有时候没人说话，牛牛自己突然蹦出来几句话

哈，是主动发言功能！内容同样从群聊里学来的！

### 怎么教牛牛说话呢？

正常聊天即可，牛牛会自动学。

如果想强行教的话，可以这样：

```text
—— 牛牛你好
—— 你好呀
—— 牛牛你好
—— 你好呀
—— 牛牛你好
—— 你好呀
```

如此重复 3 次以上，下一次再发送 “牛牛你好”，牛牛即会回复 “你好呀”

### 牛牛说了一些不合适的话，要怎么删除？

群管理员 **回复** 牛牛说的那句话 “不可以” 或直接撤回对应的消息即可，同样的若超过 N 个群都禁止了这句话，就会作为全局禁止，在任何群都不发




## 牛牛的一些其他小功能

- `牛牛喝酒` 进入狂暴醉酒状态，此时话会变多，轮盘会变为三颗子弹。
- 随机修改自己的群名片为近期发言的人，夺舍！
- `牛牛做梦` 别载着理发店
- `牛牛我问你` 调用文心模型简单问答
- `牛牛锐评一下` 巨好玩的，调用ds-r1模型进行中肯的、一针见血的评价
- `牛牛唱歌` 随机从资源库内挑选一个音频以语音形式发送出去
- `牛牛轮盘` 开枪，砰！需要给牛牛管理员才能使用，目前只做了禁言模式，主要我觉得也没人玩踢人的



## 🙏 致谢
- 原始项目 [Pallas-Bot](https://github.com/MistEO/Pallas-Bot)
- 基于原项目提炼的插件版本 [nonebot-plugin-pallas-repeater](https://github.com/Redmomn/nonebot-plugin-pallas-repeater)

感谢以上两位大神，我只是cv过来然后做了些简单的改动，在其基础上修复了一些bug以及扩充功能，包括重新实现最原初牛牛的一些其他功能。

## 📄 协议
本项目采用 [MIT License](LICENSE)
