# 配置文件示例
# 复制此文件为 config.py 并填入你的配置
# 注意: config.py 已在 .gitignore 中，不会上传到Git

# Telegram Bot配置
# 创建Bot: 在Telegram中搜索 @BotFather，发送 /newbot
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
# 获取Chat ID: 向你的bot发送消息，然后访问 https://api.telegram.org/bot<TOKEN>/getUpdates
TELEGRAM_CHAT_ID = "your_chat_id_here"

# 监控的球队名称（包含各种可能的别名）
# 北京北汽（Beijing Ducks）- 原北京首钢，北京历史最悠久的球队
# 北京控股（Beijing Royal Fighters）- 北控男篮
TEAM_NAMES = {
    "北京北汽": [
        "北京北汽",
        "北京首钢",
        "首钢",
        "北汽",
        "北京鸭",
        "Beijing Ducks",
        "Ducks",
        "北京队",
    ],
    "北京控股": [
        "北京控股",
        "北控",
        "北京北控",
        "北控男篮",
        "Beijing Royal Fighters",
        "Royal Fighters",
    ],
}

# 通知时间（多伦多时间，24小时制）
# 默认晚上8点（20:00）
NOTIFICATION_HOUR = 20

# 监控的赛季
SEASON = "2025-2026"

