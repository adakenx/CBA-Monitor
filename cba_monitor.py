#!/usr/bin/env python3
"""
CBA篮球比赛监控系统
监控北京北汽和北京控股的比赛，在比赛前一天通过Telegram推送通知

监控目标：
1. 北京北汽（Beijing Ducks）- 原北京首钢
2. 北京控股（Beijing Royal Fighters）- 北控男篮

推送时间：比赛前一天 多伦多时间 20:00
"""

import requests
import json
import re
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TEAM_NAMES,
    NOTIFICATION_HOUR,
)

# 时区定义
TZ_BEIJING = ZoneInfo("Asia/Shanghai")
TZ_TORONTO = ZoneInfo("America/Toronto")

# CBA赛程数据源
CBA_SCHEDULE_URLS = {
    "cba_official": "https://www.cbaleague.com",
    "hupu": "https://cba.hupu.com",
}

# 赛程更新间隔（天）
SCHEDULE_UPDATE_INTERVAL = 7  # 每周更新一次


class CBAMonitor:
    """CBA比赛监控类"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.team_names = TEAM_NAMES
        self.schedule_file = "schedule.json"
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.schedule_path = os.path.join(self.script_dir, self.schedule_file)
    
    def log(self, msg):
        """打印带时间戳的日志"""
        now = datetime.now(TZ_TORONTO)
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')} Toronto] {msg}")
    
    def load_local_schedule(self):
        """从本地JSON文件加载赛程"""
        try:
            with open(self.schedule_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.log(f"从本地文件加载了 {len(data.get('games', []))} 场比赛")
                return data
        except FileNotFoundError:
            self.log("本地赛程文件不存在")
            return {"games": [], "last_updated": None}
        except json.JSONDecodeError as e:
            self.log(f"本地赛程文件格式错误: {e}")
            return {"games": [], "last_updated": None}
    
    def save_local_schedule(self, games, source="web"):
        """保存赛程到本地JSON文件"""
        data = {
            "season": "2025-2026",
            "last_updated": datetime.now(TZ_BEIJING).strftime('%Y-%m-%d %H:%M:%S'),
            "update_source": source,
            "note": "此文件由程序自动更新，也可手动编辑添加比赛。",
            "games": games
        }
        
        try:
            with open(self.schedule_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log(f"已保存 {len(games)} 场比赛到本地文件")
            return True
        except Exception as e:
            self.log(f"保存赛程文件失败: {e}")
            return False
    
    def should_update_schedule(self):
        """检查是否需要更新赛程"""
        data = self.load_local_schedule()
        last_updated = data.get('last_updated')
        
        if not last_updated:
            self.log("本地赛程无更新记录，需要更新")
            return True
        
        try:
            # 解析上次更新时间
            last_update_date = datetime.strptime(last_updated.split()[0], '%Y-%m-%d')
            days_since_update = (datetime.now() - last_update_date).days
            
            if days_since_update >= SCHEDULE_UPDATE_INTERVAL:
                self.log(f"距离上次更新已 {days_since_update} 天，需要更新")
                return True
            else:
                self.log(f"距离上次更新 {days_since_update} 天，暂不需要更新")
                return False
        except Exception as e:
            self.log(f"解析更新时间失败: {e}，执行更新")
            return True
    
    def fetch_schedule_from_web(self):
        """从网页爬取赛程数据"""
        all_games = []
        
        # 尝试从CBA官网获取
        try:
            games = self._fetch_from_cba_official()
            if games:
                self.log(f"从CBA官网获取了 {len(games)} 场比赛")
                all_games.extend(games)
        except Exception as e:
            self.log(f"从CBA官网获取失败: {e}")
        
        # 尝试从虎扑获取
        try:
            games = self._fetch_from_hupu()
            if games:
                self.log(f"从虎扑获取了 {len(games)} 场比赛")
                # 合并去重
                for game in games:
                    if not self._is_duplicate_game(game, all_games):
                        all_games.append(game)
        except Exception as e:
            self.log(f"从虎扑获取失败: {e}")
        
        return all_games
    
    def _is_duplicate_game(self, game, games_list):
        """检查比赛是否重复"""
        for existing in games_list:
            if (existing.get('date') == game.get('date') and
                existing.get('home_team') == game.get('home_team') and
                existing.get('away_team') == game.get('away_team')):
                return True
        return False
    
    def _fetch_from_cba_official(self):
        """从CBA官网爬取赛程"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 尝试API接口
        api_urls = [
            "https://www.cbaleague.com/api/schedule",
            "https://www.cbaleague.com/api/match/list",
        ]
        
        for url in api_urls:
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    games = self._parse_cba_api_data(data)
                    if games:
                        return games
            except:
                continue
        
        # 尝试爬取HTML页面
        html_urls = [
            "https://www.cbaleague.com/schedule",
            "https://www.cbaleague.com/match",
        ]
        
        for url in html_urls:
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    games = self._parse_cba_html(response.text)
                    if games:
                        return games
            except:
                continue
        
        return []
    
    def _fetch_from_hupu(self):
        """从虎扑爬取赛程"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        urls = [
            "https://cba.hupu.com/schedule",
            "https://cba.hupu.com/schedule/2025-2026",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    games = self._parse_hupu_html(response.text)
                    if games:
                        return games
            except:
                continue
        
        return []
    
    def _parse_cba_api_data(self, data):
        """解析CBA官网API数据"""
        games = []
        
        # 尝试不同的数据结构
        game_list = []
        if isinstance(data, dict):
            game_list = data.get('data', data.get('list', data.get('matches', [])))
        elif isinstance(data, list):
            game_list = data
        
        for item in game_list:
            try:
                game = {
                    'date': item.get('date', item.get('matchDate', '')),
                    'time': item.get('time', item.get('matchTime', '19:35')),
                    'home_team': item.get('home', item.get('homeTeam', item.get('homeName', ''))),
                    'away_team': item.get('away', item.get('awayTeam', item.get('awayName', ''))),
                    'venue': item.get('venue', item.get('stadium', '')),
                    'broadcast': item.get('broadcast', item.get('tv', '')),
                }
                
                # 检查是否是目标球队
                if self._is_target_team_game(game):
                    games.append(game)
            except:
                continue
        
        return games
    
    def _parse_cba_html(self, html):
        """解析CBA官网HTML页面"""
        games = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试多种选择器
        selectors = [
            'div.schedule-item',
            'div.match-item',
            'tr.match-row',
            'div[class*="game"]',
            'div[class*="match"]',
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    game = self._extract_game_from_element(item)
                    if game and self._is_target_team_game(game):
                        games.append(game)
                if games:
                    break
        
        return games
    
    def _parse_hupu_html(self, html):
        """解析虎扑HTML页面"""
        games = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 虎扑赛程页面结构
        selectors = [
            'tr.match',
            'div.schedule-match',
            'div.game-item',
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    game = self._extract_game_from_element(item)
                    if game and self._is_target_team_game(game):
                        games.append(game)
                if games:
                    break
        
        return games
    
    def _extract_game_from_element(self, element):
        """从HTML元素提取比赛信息"""
        text = element.get_text(separator=' ', strip=True)
        
        # 日期模式
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{1,2}月\d{1,2}日)',
        ]
        
        date_str = None
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                break
        
        if not date_str:
            return None
        
        # 标准化日期格式
        if '月' in date_str:
            # 转换中文日期
            year = datetime.now().year
            month = int(re.search(r'(\d+)月', date_str).group(1))
            day = int(re.search(r'(\d+)日', date_str).group(1))
            # 如果月份小于当前月份，可能是明年
            if month < datetime.now().month:
                year += 1
            date_str = f"{year}-{month:02d}-{day:02d}"
        else:
            date_str = date_str.replace('/', '-')
        
        # 时间模式
        time_match = re.search(r'(\d{1,2}:\d{2})', text)
        time_str = time_match.group(1) if time_match else '19:35'
        
        # 提取球队名称
        home_team = ""
        away_team = ""
        
        for team_key, aliases in self.team_names.items():
            for alias in aliases:
                if alias in text:
                    if not home_team:
                        home_team = team_key
                    elif not away_team:
                        away_team = team_key
                    break
        
        if not home_team:
            return None
        
        return {
            'date': date_str,
            'time': time_str,
            'home_team': home_team,
            'away_team': away_team or '对手待定',
            'venue': '',
            'broadcast': '',
        }
    
    def _is_target_team_game(self, game):
        """检查是否是目标球队的比赛"""
        home = game.get('home_team', '')
        away = game.get('away_team', '')
        
        for team_key, aliases in self.team_names.items():
            # 检查球队名是否匹配
            if home == team_key or away == team_key:
                return True
            # 检查别名是否在球队名中
            for alias in aliases:
                if alias in home or alias in away:
                    return True
        
        return False
    
    def update_schedule(self, force=False):
        """更新赛程数据"""
        if not force and not self.should_update_schedule():
            return False
        
        self.log("开始更新赛程数据...")
        
        # 获取网络数据
        web_games = self.fetch_schedule_from_web()
        
        if web_games:
            # 加载本地数据
            local_data = self.load_local_schedule()
            local_games = local_data.get('games', [])
            
            # 合并数据（保留本地手动添加的比赛）
            merged_games = web_games.copy()
            for local_game in local_games:
                if not self._is_duplicate_game(local_game, merged_games):
                    # 检查是否是未来的比赛
                    game_date = local_game.get('date', '')
                    try:
                        game_dt = datetime.strptime(game_date, '%Y-%m-%d')
                        if game_dt >= datetime.now() - timedelta(days=1):
                            merged_games.append(local_game)
                    except:
                        continue
            
            # 按日期排序
            merged_games.sort(key=lambda x: x.get('date', ''))
            
            # 保存更新后的数据
            self.save_local_schedule(merged_games, "web+local")
            self.log(f"赛程更新完成，共 {len(merged_games)} 场比赛")
            return True
        else:
            self.log("网络获取失败，保留本地数据")
            # 更新时间戳，避免频繁重试
            local_data = self.load_local_schedule()
            local_games = local_data.get('games', [])
            self.save_local_schedule(local_games, "local_only")
            return False
    
    def get_schedule(self):
        """获取赛程数据"""
        # 检查是否需要更新
        self.update_schedule()
        
        # 加载本地数据
        data = self.load_local_schedule()
        return data.get('games', [])
    
    def filter_target_games(self, games):
        """筛选目标球队的比赛"""
        target_games = []
        
        for game in games:
            if self._is_target_team_game(game):
                target_games.append(game)
        
        return target_games
    
    def get_tomorrow_games(self, games):
        """获取明天（北京时间）的比赛"""
        now_beijing = datetime.now(TZ_BEIJING)
        tomorrow_beijing = now_beijing + timedelta(days=1)
        tomorrow_str = tomorrow_beijing.strftime('%Y-%m-%d')
        
        tomorrow_games = []
        for game in games:
            game_date = game.get('date', '').replace('/', '-')
            if game_date == tomorrow_str:
                tomorrow_games.append(game)
        
        return tomorrow_games
    
    def get_broadcast_info(self, game):
        """获取直播信息"""
        if game.get('broadcast'):
            return game['broadcast']
        
        # 默认直播平台提示
        return "CCTV-5/CCTV-5+、咪咕视频、央视频、抖音（请以实际播出为准）"
    
    def format_game_message(self, games):
        """格式化比赛通知消息"""
        if not games:
            return None
        
        now_beijing = datetime.now(TZ_BEIJING)
        tomorrow_beijing = now_beijing + timedelta(days=1)
        
        # 中文星期
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_cn = weekdays[tomorrow_beijing.weekday()]
        
        message = "🏀 <b>CBA比赛提醒</b>\n\n"
        message += f"📅 明天 ({tomorrow_beijing.strftime('%m月%d日')} {weekday_cn}) 有以下比赛：\n\n"
        
        for i, game in enumerate(games, 1):
            home = game.get('home_team', '未知')
            away = game.get('away_team', '未知')
            time = game.get('time', '19:35')
            venue = game.get('venue', '')
            broadcast = self.get_broadcast_info(game)
            
            message += f"<b>比赛 {i}</b>\n"
            message += f"⏰ 北京时间: {time}\n"
            message += f"🆚 {away} @ {home}\n"
            if venue:
                message += f"📍 地点: {venue}\n"
            message += f"📺 直播: {broadcast}\n\n"
        
        message += "💡 记得提前调好闹钟！"
        
        return message
    
    def send_telegram_message(self, message):
        """发送Telegram消息"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            self.log("[成功] Telegram消息已发送")
            return True
        except requests.RequestException as e:
            self.log(f"[错误] Telegram消息发送失败: {e}")
            return False
    
    def run_once(self):
        """执行一次检查"""
        self.log("=" * 50)
        self.log("开始检查CBA比赛赛程")
        self.log("=" * 50)
        
        # 获取赛程（会自动检查是否需要更新）
        self.log("获取赛程数据...")
        all_games = self.get_schedule()
        self.log(f"共获取 {len(all_games)} 场比赛数据")
        
        # 筛选目标球队
        self.log("筛选北京北汽/北京控股比赛...")
        target_games = self.filter_target_games(all_games)
        self.log(f"目标球队共有 {len(target_games)} 场比赛")
        
        # 获取明天的比赛
        self.log("检查明天是否有比赛...")
        tomorrow_games = self.get_tomorrow_games(target_games)
        
        if tomorrow_games:
            self.log(f"🏀 明天有 {len(tomorrow_games)} 场比赛！")
            message = self.format_game_message(tomorrow_games)
            if message:
                self.log("发送Telegram通知...")
                self.send_telegram_message(message)
        else:
            self.log("✅ 明天没有比赛")
        
        self.log("=" * 50)
        self.log("检查完成")
        self.log("=" * 50)
        
        return tomorrow_games


def test_connection():
    """测试连接"""
    print("=" * 50)
    print("CBA比赛监控系统 - 连接测试")
    print("=" * 50)
    
    monitor = CBAMonitor()
    
    # 显示时区信息
    print("\n1. 时区信息...")
    now_toronto = datetime.now(TZ_TORONTO)
    now_beijing = datetime.now(TZ_BEIJING)
    print(f"   多伦多时间: {now_toronto.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   北京时间:   {now_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试Telegram
    print("\n2. 测试Telegram...")
    test_msg = "🏀 CBA比赛监控测试\n\n监控球队：北京北汽、北京控股\n连接成功！"
    if monitor.send_telegram_message(test_msg):
        print("   ✅ Telegram连接成功")
    else:
        print("   ❌ Telegram连接失败")
    
    # 测试赛程获取
    print("\n3. 测试赛程获取...")
    games = monitor.get_schedule()
    if games:
        print(f"   ✅ 获取到 {len(games)} 场比赛")
        target_games = monitor.filter_target_games(games)
        print(f"   ✅ 其中目标球队 {len(target_games)} 场")
    else:
        print("   ⚠️ 未获取到赛程数据（需要手动添加到 schedule.json）")
    
    print("\n" + "=" * 50)


def test_notify():
    """测试通知功能（发送测试消息）"""
    print("=" * 50)
    print("CBA比赛监控系统 - 通知测试")
    print("=" * 50)
    
    monitor = CBAMonitor()
    
    # 创建测试比赛数据
    test_games = [
        {
            'date': (datetime.now(TZ_BEIJING) + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '19:35',
            'home_team': '北京北汽',
            'away_team': '广东东莞',
            'venue': '首钢篮球中心',
            'broadcast': 'CCTV-5、咪咕视频',
        },
        {
            'date': (datetime.now(TZ_BEIJING) + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '15:30',
            'home_team': '北京控股',
            'away_team': '浙江稠州',
            'venue': '北京奥体中心',
            'broadcast': '咪咕视频、抖音',
        }
    ]
    
    message = monitor.format_game_message(test_games)
    print("\n测试消息预览:")
    print("-" * 40)
    print(message.replace('<b>', '').replace('</b>', ''))
    print("-" * 40)
    
    print("\n发送测试通知...")
    if monitor.send_telegram_message(message):
        print("✅ 测试通知发送成功")
    else:
        print("❌ 测试通知发送失败")
    
    print("\n" + "=" * 50)


def update_schedule():
    """强制更新赛程"""
    print("=" * 50)
    print("CBA比赛监控系统 - 更新赛程")
    print("=" * 50)
    
    monitor = CBAMonitor()
    
    print("\n开始从网络获取赛程...")
    if monitor.update_schedule(force=True):
        print("✅ 赛程更新成功")
    else:
        print("⚠️ 网络获取失败，请手动更新 schedule.json")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "test":
            test_connection()
        elif cmd == "notify":
            test_notify()
        elif cmd == "once":
            monitor = CBAMonitor()
            monitor.run_once()
        elif cmd == "update":
            update_schedule()
        else:
            print("用法:")
            print("  python cba_monitor.py test     # 测试连接")
            print("  python cba_monitor.py notify   # 测试通知")
            print("  python cba_monitor.py once     # 检查比赛并推送")
            print("  python cba_monitor.py update   # 强制更新赛程")
    else:
        monitor = CBAMonitor()
        monitor.run_once()
