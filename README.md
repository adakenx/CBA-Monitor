# CBA篮球比赛监控系统

监控CBA联赛北京北汽（Beijing Ducks）和北京控股（Beijing Royal Fighters）的比赛，在比赛前一天通过 Telegram 推送通知。

## 功能特性

- 🏀 自动监控北京北汽和北京控股的比赛
- 🔄 每周自动从网络更新赛程数据
- ⏰ 比赛前一天多伦多时间20:00推送提醒
- 📺 包含直播平台信息（CCTV-5、咪咕视频、央视频、抖音等）
- 📱 Telegram 即时推送
- 🔄 支持网络爬取和本地赛程数据

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Telegram

编辑 `config.py` 文件：

#### 创建 Telegram Bot
1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 获取 Bot Token

#### 获取 Telegram Chat ID
1. 向你的 Bot 发送一条消息
2. 访问 `https://api.telegram.org/bot<你的Token>/getUpdates`
3. 在返回的 JSON 中找到 `chat.id`

### 3. 运行程序

```bash
# 测试连接
python cba_monitor.py test

# 测试通知（发送测试消息）
python cba_monitor.py notify

# 执行一次检查
python cba_monitor.py once
```

## 配置说明

在 `config.py` 中可以自定义：

```python
# Telegram配置
TELEGRAM_BOT_TOKEN = "your_token"
TELEGRAM_CHAT_ID = "your_chat_id"

# 监控的球队
TEAM_NAMES = {
    "北京首钢": ["北京首钢", "首钢", ...],
    "北京控股": ["北京控股", "北控", ...],
}

# 通知时间（多伦多时间，24小时制）
NOTIFICATION_HOUR = 20
```

## 赛程数据

程序会尝试从网络爬取赛程数据。如果爬取失败，会使用本地 `schedule.json` 文件。

### 更新本地赛程

编辑 `schedule.json`：

```json
{
  "games": [
    {
      "date": "2025-12-27",
      "time": "19:35",
      "home_team": "北京首钢",
      "away_team": "辽宁本钢",
      "venue": "首钢篮球中心",
      "broadcast": "CCTV-5、咪咕视频"
    }
  ]
}
```

## 部署到腾讯云

### 方式一：使用上传脚本

1. 编辑 `upload_to_tencent.sh`，填入服务器信息
2. 安装 sshpass：`brew install hudochenkov/sshpass/sshpass`
3. 运行：`./upload_to_tencent.sh`

### 方式二：手动部署

```bash
# 上传文件到服务器
scp -r . ubuntu@your_server:/home/ubuntu/cba-monitor/

# SSH登录服务器
ssh ubuntu@your_server

# 执行部署脚本
cd /home/ubuntu/cba-monitor
chmod +x deploy_server.sh
./deploy_server.sh
```

## 定时任务

服务器上的 cron 任务设置为每天北京时间 09:00 执行，对应多伦多时间前一天 20:00 左右。

```bash
# 查看cron任务
crontab -l | grep cba

# 编辑cron任务
crontab -e
```

## 管理命令

```bash
# 查看日志
tail -f /home/ubuntu/cba-monitor/cba.log

# 手动执行检查
cd /home/ubuntu/cba-monitor && source venv/bin/activate && python cba_monitor.py once

# 发送测试通知
python cba_monitor.py notify
```

## 注意事项

⚠️ **安全提醒**: `config.py` 包含敏感的 API 密钥，已添加到 `.gitignore`，请勿上传到代码仓库！

## 开源协议

MIT License

