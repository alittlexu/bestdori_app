# -*- coding: utf-8 -*-
import requests
import os
import logging
import time
from datetime import datetime
import json
from bs4 import BeautifulSoup
import random
import urllib.parse
import sys
import io
from tqdm import tqdm
import keyboard
import threading
import signal

try:
    from PIL import Image
    print("PIL导入成功")
except ImportError as e:
    print(f"导入PIL时出错: {e}")
    print(f"Python路径: {sys.executable}")
    print(f"sys.path: {sys.path}")

__version__ = "2.1.2"
__author__ = "Findx"
__description__ = "Bestdori卡面下载工具"

# 获取日志目录
logs_dir = os.environ.get('BESTDORI_LOGS_DIR', os.path.dirname(os.path.abspath(__file__)))

# 设置日志文件名
log_filename = os.path.join(logs_dir, f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_application_path():
    """获取应用程序路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

class BestdoriScraper:
    def __init__(self, save_dir, start_id=1, end_id=41000, selected_members=None):
        self.save_dir = save_dir
        self.start_id = start_id
        self.end_id = end_id
        self.stats = {
            "complete": 0,     # 完整下载（普通+特训）
            "normal_only": 0,  # 仅普通版本
            "trained_only": 0, # 仅特训版本
            "failed": 0,       # 下载失败
            "nonexistent": []  # 不存在的ID列表
        }
        self.control = {"stop": False}
        self.download_speed = 1.0
        self.last_state_file = os.path.join(get_application_path(), "last_state.json")
        self.successful_ids = set()
        self.last_progress_time = time.time()
        self.selected_members = selected_members or []
        
        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 首先配置日志系统
        log_file = os.path.join(save_dir, f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        self.logger = logging.getLogger('BestdoriScraper')
        self.logger.setLevel(logging.INFO)
        
        # 确保logger没有重复的处理器
        if not self.logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(console_handler)
        
        # 添加乐团和人物的映射信息
        self.band_info = {
            "Poppin'Party": {
                "folder_name": "Poppin'Party",
                "members": {
                    (1001, 2000): {"name": "Kasumi", "jp_name": "户山香澄"},
                    (2001, 3000): {"name": "Tae", "jp_name": "花园多惠"},
                    (3001, 4000): {"name": "Rimi", "jp_name": "牛込里美"},
                    (4001, 5000): {"name": "Saya", "jp_name": "山吹沙绫"},
                    (5001, 5999): {"name": "Arisa", "jp_name": "市谷有咲"}
                }
            },
            "Afterglow": {
                "folder_name": "Afterglow",
                "members": {
                    (6001, 7000): {"name": "Ran", "jp_name": "美竹兰"},
                    (7001, 8000): {"name": "Moca", "jp_name": "青叶摩卡"},
                    (8001, 9000): {"name": "Himari", "jp_name": "上原绯玛丽"},
                    (9001, 10000): {"name": "Tomoe", "jp_name": "宇田川巴"},
                    (10001, 10999): {"name": "Tsugumi", "jp_name": "羽泽鸫"}
                }
            },
            "Hello Happy World": {
                "folder_name": "Hello Happy World",
                "members": {
                    (11001, 12000): {"name": "Kokoro", "jp_name": "弦卷心"},
                    (12001, 13000): {"name": "Kaoru", "jp_name": "濑田薰"},
                    (13001, 14000): {"name": "Hagumi", "jp_name": "北泽育美"},
                    (14001, 15000): {"name": "Kano", "jp_name": "松原花音"},
                    (15001, 15999): {"name": "Misaki", "jp_name": "奥泽美咲"}
                }
            },
            "Pastel*Palettes": {
                "folder_name": "Pastel Palettes",
                "members": {
                    (16001, 17000): {"name": "Aya", "jp_name": "丸山彩"},
                    (17001, 18000): {"name": "Hina", "jp_name": "冰川日菜"},
                    (18001, 19000): {"name": "Chisato", "jp_name": "白鹭千圣"},
                    (19001, 20000): {"name": "Maya", "jp_name": "大和麻弥"},
                    (20001, 20999): {"name": "Eve", "jp_name": "若宫伊芙"}
                }
            },
            "Roselia": {
                "folder_name": "Roselia",
                "members": {
                    (21001, 22000): {"name": "Yukina", "jp_name": "湊友希那"},
                    (22001, 23000): {"name": "Sayo", "jp_name": "氷川纱夜"},
                    (23001, 24000): {"name": "Lisa", "jp_name": "今井莉莎"},
                    (24001, 25000): {"name": "Ako", "jp_name": "宇田川亚子"},
                    (25001, 25999): {"name": "Rinko", "jp_name": "白金燐子"}
                }
            },
            "Morfonica": {
                "folder_name": "Morfonica",
                "members": {
                    (26001, 27000): {"name": "Mashiro", "jp_name": "仓田真白"},
                    (27001, 28000): {"name": "Toko", "jp_name": "桐谷透子"},
                    (28001, 29000): {"name": "Nanami", "jp_name": "广町七深"},
                    (29001, 30000): {"name": "Tsukushi", "jp_name": "二叶筑紫"},
                    (30001, 30999): {"name": "Rui", "jp_name": "八潮瑠唯"}
                }
            },
            "RAISE A SUILEN": {
                "folder_name": "RAISE_A_SUILEN",
                "members": {
                    (31001, 32000): {"name": "Layer", "jp_name": "LAYER"},
                    (32001, 33000): {"name": "Lock", "jp_name": "LOCK"},
                    (33001, 34000): {"name": "Masking", "jp_name": "MASKING"},
                    (34001, 35000): {"name": "Pareo", "jp_name": "PAREO"},
                    (35001, 35999): {"name": "Chu2", "jp_name": "Chu²"}
                }
            },
            "MyGO!!!!!": {
                "folder_name": "MyGO!!!!!",
                "members": {
                    (36001, 37000): {"name": "Tomorin", "jp_name": "高松灯"},
                    (37001, 38000): {"name": "Ano", "jp_name": "千早爱音"},
                    (38001, 39000): {"name": "Rana", "jp_name": "要乐奈"},
                    (39001, 40000): {"name": "Soyo", "jp_name": "长崎素世"},
                    (40001, 40999): {"name": "Riki", "jp_name": "椎名立希"}
                }
            }
        }
        
        # 构建组合范围映射
        self.group_ranges = {}
        for band_name, band_data in self.band_info.items():
            min_start = float('inf')
            max_end = 0
            for (start, end), _ in band_data["members"].items():
                min_start = min(min_start, start)
                max_end = max(max_end, end)
            self.group_ranges[band_name] = (min_start, max_end)
        
        # 信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        # 最后创建会话
        self.session = self._create_session()
    
    def get_group_name(self, card_id):
        """根据卡牌ID获取所属组合名称"""
        for band_name, band_data in self.band_info.items():
            for id_range, _ in band_data["members"].items():
                start, end = id_range
                if start <= card_id <= end:
                    return band_name
        return None
    
    def get_next_valid_id(self, current_id):
        """获取下一个可能的有效ID"""
        # 如果当前ID已经超过结束ID，直接返回结束ID+1
        if current_id >= self.end_id:
            return self.end_id + 1
            
        # 如果有选定的成员列表，使用它来确定下一个ID
        if self.selected_members:
            current_member = None
            next_member = None
            
            # 找到当前ID对应的成员编号
            for i in range(1, 41):
                start = (i - 1) * 1000 + 1001
                end = start + 999
                if start <= current_id <= end:
                    current_member = i
                    break
            
            if current_member is not None:
                # 在选定的成员列表中找到下一个成员
                for member_id in sorted(self.selected_members):
                    if member_id > current_member:
                        next_member = member_id
                        break
                
                if next_member:
                    # 返回下一个选定成员的起始ID
                    next_start = (next_member - 1) * 1000 + 1001
                    # 确保不会超过结束ID
                    if next_start > self.end_id:
                        return self.end_id + 1
                    return next_start
            
            # 如果没有找到下一个成员，返回结束ID+1
            return self.end_id + 1
        
        # 如果没有选定的成员列表，使用原有的逻辑
        member_info = self.get_member_info(current_id)
        if not member_info:
            # 如果找不到成员信息，直接返回当前ID+1，但不超过结束ID
            return min(current_id + 1, self.end_id + 1)
        
        # 获取当前成员所在乐团的所有ID范围
        current_band = member_info["band_name"]
        band_data = self.band_info[current_band]
        
        # 获取当前成员的ID范围
        current_range = None
        for id_range, _ in band_data["members"].items():
            start, end = id_range
            if start <= current_id <= end:
                current_range = (start, end)
                break
        
        if not current_range:
            # 如果找不到范围，直接返回当前ID+1，但不超过结束ID
            return min(current_id + 1, self.end_id + 1)
        
        # 计算当前成员的基础ID
        current_member_base = ((current_id - current_range[0]) // 1000) * 1000 + current_range[0]
        
        # 计算下一个成员的基础ID
        next_member_base = current_member_base + 1000
        
        # 检查是否在当前乐团范围内
        for id_range, _ in band_data["members"].items():
            start, end = id_range
            if start == next_member_base:
                # 确保不会超过结束ID
                if next_member_base > self.end_id:
                    return self.end_id + 1
                return next_member_base
        
        # 如果超出当前乐团范围，查找下一个乐团的起始ID
        found_current = False
        for band_name, band_data in self.band_info.items():
            for id_range, _ in band_data["members"].items():
                start, end = id_range
                if found_current and start > current_id:
                    # 确保不会超过结束ID
                    if start > self.end_id:
                        return self.end_id + 1
                    return start
                if start <= current_id <= end:
                    found_current = True
                
        # 如果没有找到下一个有效的ID，返回结束ID+1
        return self.end_id + 1

    def get_member_info(self, card_id):
        """获取卡牌对应的乐团和成员信息"""
        for band_name, band_data in self.band_info.items():
            for id_range, member_data in band_data["members"].items():
                start, end = id_range
                if start <= card_id <= end:
                    return {
                        "band_name": band_name,
                        "band_folder": band_data["folder_name"],
                        "member_name": member_data["name"],
                        "member_jp_name": member_data["jp_name"]
                    }
        return None

    def ensure_directories(self, card_id):
        """确保所需的目录结构存在"""
        member_info = self.get_member_info(card_id)
        if not member_info:
            return None

        # 获取工作目录的根路径
        root_path = os.path.dirname(self.save_dir)
        
        # 检查是否存在乐队文件夹
        band_path = os.path.join(root_path, member_info["band_folder"])
        if not os.path.exists(band_path):
            os.makedirs(band_path, exist_ok=True)
            self.logger.info(f"创建乐队文件夹: {member_info['band_folder']}")

        # 检查是否存在成员文件夹
        member_path = os.path.join(band_path, member_info["member_name"])
        if not os.path.exists(member_path):
            os.makedirs(member_path, exist_ok=True)
            self.logger.info(f"创建成员文件夹: {member_info['member_name']}")

        return member_path

    def process_card(self, card_id):
        """处理单张卡牌"""
        servers = ["jp", "en", "tw", "cn", "kr"]
        
        # 获取保存路径
        save_path_base = self.ensure_directories(card_id)
        if not save_path_base:
            return False
            
        member_info = self.get_member_info(card_id)
        
        # 快速检查卡牌是否存在
        card_exists = False
        for server in servers:
            # 首先只检查normal版本，因为每张卡至少会有normal版本
            check_url = f"https://bestdori.com/assets/{server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_normal.png"
            try:
                response = self.session.head(check_url, timeout=3)
                if response.status_code == 200:
                    card_exists = True
                    break
            except:
                continue
        
        if not card_exists:
            self.stats["nonexistent"].append(card_id)
            self.logger.debug(f"ID {card_id} ({member_info['band_name']} - {member_info['member_jp_name']}) 不存在对应的卡牌")
            return False
            
        normal_success = False
        trained_success = False
        
        # 已确认卡牌存在，尝试下载
        for server in servers:
            if normal_success:
                break
            
            url = f"https://bestdori.com/assets/{server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_normal.png"
            save_path = os.path.join(save_path_base, f"{card_id}_normal.png")
            
            if self.download_image(url, save_path):
                normal_success = True
                # 立即尝试下载trained状态
                trained_url = f"https://bestdori.com/assets/{server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_after_training.png"
                trained_save_path = os.path.join(save_path_base, f"{card_id}_trained.png")
                
                if self.download_image(trained_url, trained_save_path):
                    trained_success = True
                else:
                    # 快速检查其他服务器
                    for other_server in servers:
                        if other_server != server:
                            trained_url = f"https://bestdori.com/assets/{other_server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_after_training.png"
                            if self.download_image(trained_url, trained_save_path, quick_check=True):
                                trained_success = True
                                break
                
                # 更新统计信息
                if normal_success and trained_success:
                    self.stats["complete"] += 1
                    status = "普通和特训后版本"
                elif normal_success:
                    self.stats["normal_only"] += 1
                    status = "仅普通版本"
                
                self.logger.info(f"卡牌 {card_id} ({member_info['band_name']} - {member_info['member_jp_name']}) - {status}已下载")
                self.successful_ids.add(card_id)
                return True
        
        # 如果normal下载失败，尝试只下载trained版本
        if not normal_success:
            for server in servers:
                trained_url = f"https://bestdori.com/assets/{server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_after_training.png"
                trained_save_path = os.path.join(save_path_base, f"{card_id}_trained.png")
                
                if self.download_image(trained_url, trained_save_path):
                    trained_success = True
                    self.stats["trained_only"] += 1
                    status = "仅特训版本"
                    self.logger.info(f"卡牌 {card_id} ({member_info['band_name']} - {member_info['member_jp_name']}) - {status}已下载")
                    self.successful_ids.add(card_id)
                    return True
        
        # 如果都失败了，记录为下载失败
        if not (normal_success or trained_success):
            self.stats["failed"] += 1
            self.logger.info(f"卡牌 {card_id} ({member_info['band_name']} - {member_info['member_jp_name']}) - 下载失败")
        
        return False

    def run(self):
        """运行下载器，增加智能跳转和用户交互"""
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 加载状态
        state = self.load_state()
        # 只有当状态文件存在且当前下载范围与上次的下载范围相同时才提示继续
        if state and state.get("start_id") == self.start_id and state.get("end_id") == self.end_id:
            if input("发现上次的下载记录，是否继续？(y/n): ").lower().strip() == 'y':
                self.current_id = state["last_id"]
                self.stats = state["stats"]
                self.successful_ids = set(state["successful_ids"])
            else:
                self.current_id = self.start_id
                # 如果选择不继续，删除状态文件
                if os.path.exists(self.last_state_file):
                    try:
                        os.remove(self.last_state_file)
                    except:
                        pass
        else:
            self.current_id = self.start_id
            # 如果状态文件存在但范围不同，删除它
            if os.path.exists(self.last_state_file):
                try:
                    os.remove(self.last_state_file)
                except:
                    pass
        
        self.logger.info("\n=== 控制说明 ===")
        self.logger.info("1. 使用 Ctrl+C 保存并退出")
        self.logger.info("2. 按回车键手动跳转到下一个角色")
        self.logger.info("3. 输入数字+回车跳转到指定ID")
        self.logger.info("============\n")
        
        try:
            consecutive_fails = 0
            last_success_id = self.current_id
            current_character_base = ((self.current_id - 1) // 1000) * 1000 + 1
            empty_id_streak = 0  # 连续空ID计数
            
            while self.current_id <= self.end_id and not self.control["stop"]:
                group_name = self.get_group_name(self.current_id) or "未知组合"
                self._update_progress(self.current_id, group_name)
                
                if self.process_card(self.current_id):
                    consecutive_fails = 0
                    empty_id_streak = 0
                    last_success_id = self.current_id
                else:
                    consecutive_fails += 1
                    
                    # 如果是不存在的卡牌ID
                    if self.current_id in self.stats["nonexistent"]:
                        empty_id_streak += 1
                    
                    # 连续5次失败，直接跳转到下一个角色
                    if consecutive_fails >= 5:
                        next_id = self.get_next_valid_id(last_success_id)
                        current_character_end = current_character_base + 999
                        
                        self.logger.info(f"\n检测到连续{consecutive_fails}次失败，判定当前角色卡牌已扫描完毕")
                        self.logger.info(f"从 {self.current_id} 跳转至下一个角色ID: {next_id}")
                        
                        self.current_id = next_id
                        consecutive_fails = 0
                        empty_id_streak = 0
                        current_character_base = ((self.current_id - 1) // 1000) * 1000 + 1
                        continue
                
                self.current_id += 1
                
        except KeyboardInterrupt:
            self.logger.info("\n正在保存进度...")
            self.save_state()
            self.logger.info("进度已保存")
        except Exception as e:
            self.logger.error(f"程序异常退出: {e}")
        finally:
            # 只有在正常完成下载时才删除状态文件
            if not self.control["stop"] and self.current_id > self.end_id:
                if os.path.exists(self.last_state_file):
                    try:
                        os.remove(self.last_state_file)
                        self.logger.info("已清理下载记录")
                    except Exception as e:
                        self.logger.error(f"清理下载记录失败: {e}")
            else:
                self.save_state()
            self._show_statistics()

    def quick_check_card_exists(self, card_id):
        """快速检查卡牌是否存在"""
        servers = ["jp", "en", "tw", "cn", "kr"]
        for server in servers:
            check_url = f"https://bestdori.com/assets/{server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_normal.png"
            try:
                response = self.session.head(check_url, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                continue
        return False
        
    def _create_session(self):
        """创建请求会话"""
        session = requests.Session()
        
        # 通用请求头
        common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5',
            'Connection': 'keep-alive',
            'Referer': 'https://bestdori.com/info/cards',
            'Cache-Control': 'no-cache'
        }
        session.headers.update(common_headers)
        
        # 初始化会话，获取必要的cookie
        try:
            self.logger.info("初始化会话...")
            session.get('https://bestdori.com', timeout=10)
            session.get('https://bestdori.com/info/cards', timeout=10)
            self.logger.info("会话初始化成功")
        except Exception as e:
            self.logger.error(f"会话初始化失败: {str(e)}")
        
        return session

    def clean_filename(self, filename):
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename.strip()

    def try_direct_image_download(self, card_id):
        """直接尝试下载图片，跳过页面解析"""
        # 直接构建可能的图片URL
        image_urls = []
        
        # 尝试不同的资源ID格式
        resource_ids = [
            f"res{str(card_id).zfill(6)}",  # 例如: res000123
            f"res0{str(card_id).zfill(5)}"   # 例如: res001234
        ]
        
        # 尝试不同的服务器
        servers = ["jp", "en", "tw", "cn", "kr"]
        
        # 构建所有可能的URL组合
        for resource_id in resource_ids:
            for server in servers:
                base_url = f"https://bestdori.com/assets/{server}/characters/resourceset/"
                image_urls.append(f"{base_url}{resource_id}_rip/card_normal.png")
                image_urls.append(f"{base_url}{resource_id}_rip/card_after_training.png")
        
        # 尝试下载图片
        card_name = f"card_{card_id}"
        success = False
        
        # 修改：尝试下载所有可能的图片，不在第一次成功后就停止
        download_count = 0
        for idx, url in enumerate(image_urls, 1):
            # 为不同类型的图片使用不同的文件名
            if "card_normal.png" in url:
                save_path = os.path.join(self.save_dir, f"{card_name}_normal.png")
            elif "card_after_training.png" in url:
                save_path = os.path.join(self.save_dir, f"{card_name}_trained.png")
            else:
                save_path = os.path.join(self.save_dir, f"{card_name}_{idx}.png")
                
            if self.download_image(url, save_path):
                success = True
                download_count += 1
                # 如果已经找到了两张图片（普通和特训后），可以提前结束
                if download_count >= 2:
                    break
        
        return success

    def download_image(self, url, save_path, quick_check=False, retries=2):
        """下载图片，增加快速检查模式"""
        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            if file_size > 100000:
                return True
            os.remove(save_path)
        
        attempts = 1 if quick_check else retries
        
        for attempt in range(attempts):
            try:
                if not quick_check:
                    time.sleep(random.uniform(0.2, 0.5) / self.download_speed)
                
                headers = {
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Referer': 'https://bestdori.com/info/cards'
                }
                
                response = self.session.get(url, headers=headers, timeout=5 if quick_check else 10, stream=True)
                
                if response.status_code == 404:
                    return False
                
                if not response.headers.get('content-type', '').startswith('image/'):
                    return False
                
                img_data = response.content
                img_size = len(img_data)
                
                if img_size < 100000:
                    return False
                
                img = Image.open(io.BytesIO(img_data))
                width, height = img.size
                
                if width != 1334 or height != 1002:
                    return False
                
                with open(save_path, 'wb') as f:
                    f.write(img_data)
                
                return True
                
            except Exception as e:
                if not quick_check:
                    self.logger.debug(f"下载图片时出错: {e}")
                continue
        
        return False
        
    def save_state(self):
        """保存当前状态"""
        state = {
            "last_id": self.current_id,
            "stats": self.stats,
            "successful_ids": list(self.successful_ids),
            "start_id": self.start_id,  # 添加起始ID
            "end_id": self.end_id       # 添加结束ID
        }
        with open(self.last_state_file, 'w') as f:
            json.dump(state, f)
            
    def load_state(self):
        """加载上次的状态"""
        if os.path.exists(self.last_state_file):
            try:
                with open(self.last_state_file, 'r') as f:
                    state = json.load(f)
                return state
            except:
                return None
        return None

    def _handle_signal(self, signum, frame):
        """处理信号"""
        if signum in (signal.SIGINT, signal.SIGTERM):
            if not self.control["stop"]:
                self.logger.info("\n正在保存进度并退出...")
                self.control["stop"] = True
                self.save_state()
                self.logger.info("进度已保存")

    def _update_progress(self, current_id, group_name):
        """更新进度信息"""
        current_time = time.time()
        # 每5秒更新一次进度
        if current_time - self.last_progress_time >= 5:
            total = self.end_id - self.start_id + 1
            current = current_id - self.start_id + 1
            progress = (current / total) * 100
            
            self.logger.info(
                f"进度: {progress:.1f}% | "
                f"当前ID: {current_id} | "
                f"组合: {group_name} | "
                f"成功: {self.stats['complete'] + self.stats['normal_only']} | "
                f"失败: {self.stats['failed']}"
            )
            self.last_progress_time = current_time

    def _show_statistics(self):
        """显示统计信息"""
        total_processed = self.stats["complete"] + self.stats["normal_only"] + self.stats["trained_only"] + self.stats["failed"]
        
        self.logger.info("\n===== 下载统计 =====")
        self.logger.info(f"总计处理: {total_processed} 张卡牌")
        self.logger.info(f"├─ 完整下载: {self.stats['complete']} 张")
        self.logger.info(f"├─ 仅普通版本: {self.stats['normal_only']} 张")
        self.logger.info(f"├─ 仅特训版本: {self.stats['trained_only']} 张")
        self.logger.info(f"└─ 下载失败: {self.stats['failed']} 张")
        
        if self.stats["nonexistent"]:
            # 对不存在的ID进行区间合并
            ranges = []
            current_range = [self.stats["nonexistent"][0], self.stats["nonexistent"][0]]
            
            for id in sorted(self.stats["nonexistent"][1:]):
                if id == current_range[1] + 1:
                    current_range[1] = id
                else:
                    ranges.append(current_range)
                    current_range = [id, id]
            ranges.append(current_range)
            
            self.logger.info("\n不存在卡牌的ID区间:")
            for range_start, range_end in ranges:
                if range_start == range_end:
                    self.logger.info(f"  - {range_start}")
                else:
                    self.logger.info(f"  - {range_start} 至 {range_end}")
        
        # 保存成功下载的ID列表
        success_file = os.path.join(self.save_dir, "successful_ids.txt")
        with open(success_file, 'w', encoding='utf-8') as f:
            current_group = None
            for card_id in sorted(self.successful_ids):
                group_name = self.get_group_name(card_id)
                if group_name != current_group:
                    current_group = group_name
                    f.write(f"\n=== {group_name} ===\n")
                f.write(f"{card_id}\n")
        self.logger.info(f"\n成功下载的ID列表已保存到: {success_file}")

def load_character_list():
    """加载人物列表"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        character_list_file = os.path.join(script_dir, "character_list.json")
        
        if not os.path.exists(character_list_file):
            print("错误：找不到人物列表文件 character_list.json")
            return None
            
        with open(character_list_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载人物列表时出错: {e}")
        return None

def display_character_list(character_data):
    """显示人物列表"""
    print("\n┌─────────────────────────┐")
    print("│     选择下载范围        │")
    print("├─────────────────────────┤")
    print("│ 1. 按组合选择          │")
    print("│ 2. 按人物选择          │")
    print("│ 0. 自定义ID范围        │")
    print("└─────────────────────────┘\n")
    
    choice = input("请选择查找方式 [0/1/2]: ").strip()
    
    if choice == "1":
        print("\n┌─────────── 组合列表 ───────────┐")
        for group in character_data["groups"]:
            print(f"│ {group['id']:2d}. {group['name']:<20} │")
            print(f"│    ID范围: {group['id_range']['start']}-{group['id_range']['end']} │")
        print("└──────────────────────────────┘\n")
        
    elif choice == "2":
        for group in character_data["groups"]:
            print(f"\n┌─────────── {group['name']} ───────────┐")
            for member in group["members"]:
                print(f"│ {member['id']:2d}. {member['name']:<8} ({member['nickname']:<8}) │")
                print(f"│    ID范围: {member['id_range']['start']}-{member['id_range']['end']} │")
            print("└──────────────────────────────┘")
        
    return choice

def parse_selection(input_str):
    """解析用户输入的选择"""
    # 首先替换所有分隔符为逗号
    input_str = input_str.replace('，', ',').replace('、', ',').replace(' ', ',')
    
    # 移除空白字符（除了已经转换为逗号的空格）
    input_str = ''.join(input_str.split())
    
    # 分割输入
    parts = input_str.split(',')
    
    selected_ids = set()
    for part in parts:
        if part:  # 确保部分不是空字符串
            if '-' in part:  # 处理范围选择（如"1-5"）
                try:
                    start, end = map(int, part.split('-'))
                    selected_ids.update(range(start, end + 1))
                except ValueError:
                    continue
            else:  # 处理单个数字
                try:
                    selected_ids.add(int(part))
                except ValueError:
                    continue
                    
    return sorted(list(selected_ids))

def get_id_ranges(character_data, selection_type, selected_ids):
    """获取选定ID的范围"""
    id_ranges = []
    
    if selection_type == "1":  # 按组合选择
        for group in character_data["groups"]:
            if group["id"] in selected_ids:
                id_ranges.append(group["id_range"])
    elif selection_type == "2":  # 按人物选择
        for group in character_data["groups"]:
            for member in group["members"]:
                if member["id"] in selected_ids:
                    id_ranges.append(member["id_range"])
    
    # 合并重叠的范围
    if id_ranges:
        id_ranges.sort(key=lambda x: x["start"])
        merged = [id_ranges[0]]
        for current in id_ranges[1:]:
            if current["start"] <= merged[-1]["end"]:
                merged[-1]["end"] = max(merged[-1]["end"], current["end"])
            else:
                merged.append(current)
        return merged
    
    return []

def show_about():
    """显示关于信息"""
    print(f"\n{__description__}")
    print(f"版本: {__version__}")
    print(f"作者: {__author__}")
    
    print("\n=== 组合与人物列表 ===")
    print("1. Poppin'Party (ID: 1001-5999)")
    print("   ├─ 户山香澄 (1001-2000)")
    print("   ├─ 花园多惠 (2001-3000)")
    print("   ├─ 牛込里美 (3001-4000)")
    print("   ├─ 山吹沙绫 (4001-5000)")
    print("   └─ 市谷有咲 (5001-5999)")
    
    print("\n2. Afterglow (ID: 6001-10999)")
    print("   ├─ 美竹兰 (6001-7000)")
    print("   ├─ 青叶摩卡 (7001-8000)")
    print("   ├─ 上原绯玛丽 (8001-9000)")
    print("   ├─ 宇田川巴 (9001-10000)")
    print("   └─ 羽泽鸫 (10001-10999)")
    
    print("\n3. Hello Happy World (ID: 11001-15999)")
    print("   ├─ 弦卷心 (11001-12000)")
    print("   ├─ 濑田薰 (12001-13000)")
    print("   ├─ 北泽育美 (13001-14000)")
    print("   ├─ 松原花音 (14001-15000)")
    print("   └─ 奥泽美咲 (15001-15999)")
    
    print("\n4. Pastel*Palettes (ID: 16001-20999)")
    print("   ├─ 丸山彩 (16001-17000)")
    print("   ├─ 冰川日菜 (17001-18000)")
    print("   ├─ 白鹭千圣 (18001-19000)")
    print("   ├─ 大和麻弥 (19001-20000)")
    print("   └─ 若宫伊芙 (20001-20999)")
    
    print("\n5. Roselia (ID: 21001-25999)")
    print("   ├─ 湊友希那 (21001-22000)")
    print("   ├─ 氷川纱夜 (22001-23000)")
    print("   ├─ 今井莉莎 (23001-24000)")
    print("   ├─ 宇田川亚子 (24001-25000)")
    print("   └─ 白金燐子 (25001-25999)")
    
    print("\n6. Morfonica (ID: 26001-30999)")
    print("   ├─ 仓田真白(26001-27000)")
    print("   ├─ 桐谷透子(27001-28000)")
    print("   ├─ 广町七深 (28001-29000)")
    print("   ├─ 二叶筑紫 (29001-30000)")
    print("   └─ 八潮瑠唯 (30001-30999)")
    
    print("\n7. RAISE A SUILEN (ID: 31001-35999)")
    print("   ├─ Chu2 (31001-32000)")
    print("   ├─ LOCK (32001-33000)")
    print("   ├─ LAYER (33001-34000)")
    print("   ├─ PAREO (34001-35000)")
    print("   └─ MASKING (35001-35999)")
    
    print("\n8. MyGO!!!!! (ID: 36001-40999)")
    print("   ├─ 高松灯 (36001-37000)")
    print("   ├─ 千早爱音(37001-38000)")
    print("   ├─ 要乐奈 (38001-39000)")
    print("   ├─ 长崎素世 (39001-40000)")
    print("   └─ 椎名立希 (40001-40999)")
    
    print("\n=== 使用说明 ===")
    print("1. 选择下载方式：")
    print("   a) 输入组合编号(1-8)下载整个组合")
    print("   b) 输入具体ID范围下载指定卡牌")
    print("2. 设置下载速度(0.1-5.0)")
    print("3. 使用空格键暂停/继续")
    print("4. 使用Q键停止下载")
    print("5. 使用Ctrl+C保存并退出")
    
    print("\n=== 注意事项 ===")
    print("1. 下载的图片保存在downloads目录")
    print("2. 每次运行会创建新的子目录")
    print("3. 支持断点续传功能")
    print("4. 下载记录保存在日志文件中")

def get_character_info(member_id):
    """获取角色详细信息"""
    character_info = {
        # Poppin'Party
        1: {"name": "户山香澄", "band": "Poppin'Party", "range": (1001, 2000)},
        2: {"name": "花园多惠", "band": "Poppin'Party", "range": (2001, 3000)},
        3: {"name": "牛込里美", "band": "Poppin'Party", "range": (3001, 4000)},
        4: {"name": "山吹沙绫", "band": "Poppin'Party", "range": (4001, 5000)},
        5: {"name": "市谷有咲", "band": "Poppin'Party", "range": (5001, 5999)},
        # Afterglow
        6: {"name": "美竹兰", "band": "Afterglow", "range": (6001, 7000)},
        7: {"name": "青叶摩卡", "band": "Afterglow", "range": (7001, 8000)},
        8: {"name": "上原绯玛丽", "band": "Afterglow", "range": (8001, 9000)},
        9: {"name": "宇田川巴", "band": "Afterglow", "range": (9001, 10000)},
        10: {"name": "羽泽鸫", "band": "Afterglow", "range": (10001, 10999)},
        # Hello Happy World
        11: {"name": "弦卷心", "band": "Hello Happy World", "range": (11001, 12000)},
        12: {"name": "濑田薰", "band": "Hello Happy World", "range": (12001, 13000)},
        13: {"name": "北泽育美", "band": "Hello Happy World", "range": (13001, 14000)},
        14: {"name": "松原花音", "band": "Hello Happy World", "range": (14001, 15000)},
        15: {"name": "奥泽美咲", "band": "Hello Happy World", "range": (15001, 15999)},
        # Pastel*Palettes
        16: {"name": "丸山彩", "band": "Pastel*Palettes", "range": (16001, 17000)},
        17: {"name": "冰川日菜", "band": "Pastel*Palettes", "range": (17001, 18000)},
        18: {"name": "白鹭千圣", "band": "Pastel*Palettes", "range": (18001, 19000)},
        19: {"name": "大和麻弥", "band": "Pastel*Palettes", "range": (19001, 20000)},
        20: {"name": "若宫伊芙", "band": "Pastel*Palettes", "range": (20001, 20999)},
        # Roselia
        21: {"name": "湊友希那", "band": "Roselia", "range": (21001, 22000)},
        22: {"name": "氷川纱夜", "band": "Roselia", "range": (22001, 23000)},
        23: {"name": "今井莉莎", "band": "Roselia", "range": (23001, 24000)},
        24: {"name": "宇田川亚子", "band": "Roselia", "range": (24001, 25000)},
        25: {"name": "白金燐子", "band": "Roselia", "range": (25001, 25999)},
        # Morfonica
        26: {"name": "仓田真白", "band": "Morfonica", "range": (26001, 27000)},
        27: {"name": "桐谷透子", "band": "Morfonica", "range": (27001, 28000)},
        28: {"name": "广町七深", "band": "Morfonica", "range": (28001, 29000)},
        29: {"name": "二叶筑紫", "band": "Morfonica", "range": (29001, 30000)},
        30: {"name": "八潮瑠唯", "band": "Morfonica", "range": (30001, 30999)},
        # RAISE A SUILEN
        31: {"name": "Layer", "band": "RAISE A SUILEN", "range": (31001, 32000)},
        32: {"name": "Lock", "band": "RAISE A SUILEN", "range": (32001, 33000)},
        33: {"name": "Masking", "band": "RAISE A SUILEN", "range": (33001, 34000)},
        34: {"name": "Pareo", "band": "RAISE A SUILEN", "range": (34001, 35000)},
        35: {"name": "Chu2", "band": "RAISE A SUILEN", "range": (35001, 35999)},
        # MyGO!!!!!
        36: {"name": "高松灯", "band": "MyGO!!!!!", "range": (36001, 37000)},
        37: {"name": "千早爱音", "band": "MyGO!!!!!", "range": (37001, 38000)},
        38: {"name": "要乐奈", "band": "MyGO!!!!!", "range": (38001, 39000)},
        39: {"name": "长崎素世", "band": "MyGO!!!!!", "range": (39001, 40000)},
        40: {"name": "椎名立希", "band": "MyGO!!!!!", "range": (40001, 40999)}
    }
    return character_info.get(member_id)

def show_selected_characters(member_ids):
    """显示选中的角色信息"""
    print("\n=== 已选择的角色信息 ===")
    
    # 按乐队分组
    band_groups = {}
    for member_id in sorted(member_ids):
        info = get_character_info(member_id)
        if info:
            if info['band'] not in band_groups:
                band_groups[info['band']] = []
            band_groups[info['band']].append({
                'id': member_id,
                'name': info['name'],
                'range': info['range']
            })
    
    # 显示分组信息
    for band_name, members in band_groups.items():
        print(f"\n▶ {band_name}")
        print("  " + "─" * 50)
        for member in members:
            id_range = f"{member['range'][0]}-{member['range'][1]}"
            print(f"  ・{member['id']:2d}号 - {member['name']} ({id_range})")
        print("  " + "─" * 50)
    
    # 显示统计信息
    print("\n[ 选择统计 ]")
    print(f"・选择角色数: {len(member_ids)} 名")
    print(f"・涉及乐队数: {len(band_groups)} 个")
    for band_name, members in band_groups.items():
        print(f"  - {band_name}: {len(members)} 名")

def show_startup_info():
    """显示启动信息"""
    print("\n" + "="*50)
    print(f"欢迎使用 {__description__} v{__version__}")
    print("="*50)
    print("\n【程序说明】")
    print("本程序用于下载Bestdori的卡牌图片资源")
    print("支持按组合、角色或ID范围进行下载")
    print("\n【使用提示】")
    print("1. 下载的图片将保存在程序目录下的downloads文件夹中")
    print("2. 支持断点续传功能")
    print("3. 可自定义下载速度")
    print("4. 支持多种下载方式选择")
    print("\n【操作说明】")
    print("- Ctrl+C: 保存进度并退出")
    print("- 回车键: 手动跳转到下一个角色")
    print("- 数字+回车: 跳转到指定ID")
    print("\n【注意事项】")
    print("1. 请确保网络连接稳定")
    print("2. 下载过程中请勿关闭程序")
    print("3. 如需中途退出，请使用Ctrl+C以保存进度")
    print("\n" + "="*50 + "\n")
    print("程序初始化中，请稍候...\n")

def main():
    while True:  # 添加主循环
        try:
            show_startup_info()
            
            # 初始化变量
            member_ids = []
            start_id = 0
            end_id = 0
            
            print("\n┌─────────────────────────┐")
            print("│     选择下载范围        │")
            print("├─────────────────────────┤")
            print("│ 1. 按组合选择          │")
            print("│ 2. 按人物选择          │")
            print("│ 3. 按ID范围选择        │")
            print("└─────────────────────────┘")
            
            choice = input("\n请选择下载方式 [1/2/3]: ").strip()
            
            if choice == "1":
                print("\n=== 组合列表 ===")
                print("1. Poppin'Party (ID: 1001-5999)")
                print("2. Afterglow (ID: 6001-10999)")
                print("3. Hello Happy World (ID: 11001-15999)")
                print("4. Pastel*Palettes (ID: 16001-20999)")
                print("5. Roselia (ID: 21001-25999)")
                print("6. Morfonica (ID: 26001-30999)")
                print("7. RAISE A SUILEN (ID: 31001-35999)")
                print("8. MyGO!!!!! (ID: 36001-40999)")
                
                print("\n请输入组合编号，支持以下格式：")
                print("- 单个编号：1")
                print("- 多个编号：1,2,3 或 1、2、3 或 1 2 3")
                print("- 范围编号：1-3")
                
                group_choice = input("\n请选择要下载的组合: ").strip()
                group_ids = parse_selection(group_choice)
                
                # 根据组合编号设置ID范围
                group_ranges = {
                    1: (1001, 5999),    # Poppin'Party
                    2: (6001, 10999),   # Afterglow
                    3: (11001, 15999),  # Hello Happy World
                    4: (16001, 20999),  # Pastel*Palettes
                    5: (21001, 25999),  # Roselia
                    6: (26001, 30999),  # Morfonica
                    7: (31001, 35999),  # RAISE A SUILEN
                    8: (36001, 40999)   # MyGO!!!!!
                }
                
                if not group_ids:
                    print("未选择有效的组合，程序退出")
                    return
                
                print("\n已选择的组合：")
                for group_id in group_ids:
                    if group_id in group_ranges:
                        start, end = group_ranges[group_id]
                        print(f"组合 {group_id}: {start}-{end}")
                
                confirm = input("\n确认下载这些组合的卡牌？(y/n): ").lower().strip()
                if confirm != 'y':
                    print("已取消下载")
                    return
                
                start_id = min(group_ranges[id][0] for id in group_ids if id in group_ranges)
                end_id = max(group_ranges[id][1] for id in group_ids if id in group_ranges)
                
            elif choice == "2":
                print("\n=== 人物列表 ===")
                # Poppin'Party
                print("\n--- Poppin'Party ---")
                print("1.  户山香澄 (1001-2000)")
                print("2.  花园多惠 (2001-3000)")
                print("3.  牛込里美 (3001-4000)")
                print("4.  山吹沙绫 (4001-5000)")
                print("5.  市谷有咲 (5001-5999)")
                
                # Afterglow
                print("\n--- Afterglow ---")
                print("6.  美竹兰   (6001-7000)")
                print("7.  青叶摩卡 (7001-8000)")
                print("8.  上原绯玛丽 (8001-9000)")
                print("9.  宇田川巴 (9001-10000)")
                print("10. 羽泽鸫   (10001-10999)")
                
                # Hello Happy World
                print("\n--- Hello Happy World ---")
                print("11. 弦卷心   (11001-12000)")
                print("12. 濑田薰   (12001-13000)")
                print("13. 北泽育美 (13001-14000)")
                print("14. 松原花音 (14001-15000)")
                print("15. 奥泽美咲 (15001-15999)")
                
                # Pastel*Palettes
                print("\n--- Pastel*Palettes ---")
                print("16. 丸山彩   (16001-17000)")
                print("17. 冰川日菜 (17001-18000)")
                print("18. 白鹭千圣 (18001-19000)")
                print("19. 大和麻弥 (19001-20000)")
                print("20. 若宫伊芙 (20001-20999)")
                
                # Roselia
                print("\n--- Roselia ---")
                print("21. 湊友希那 (21001-22000)")
                print("22. 氷川纱夜 (22001-23000)")
                print("23. 今井莉莎 (23001-24000)")
                print("24. 宇田川亚子 (24001-25000)")
                print("25. 白金燐子 (25001-25999)")
                
                # Morfonica
                print("\n--- Morfonica ---")
                print("26. 仓田真白 (26001-27000)")
                print("27. 桐谷透子 (27001-28000)")
                print("28. 广町七深 (28001-29000)")
                print("29. 二叶筑紫 (29001-30000)")
                print("30. 八潮瑠唯 (30001-30999)")
                
                # RAISE A SUILEN
                print("\n--- RAISE A SUILEN ---")
                print("31. Layer   (31001-32000)")
                print("32. Lock    (32001-33000)")
                print("33. Masking (33001-34000)")
                print("34. Pareo   (34001-35000)")
                print("35. Chu2    (35001-35999)")
                
                # MyGO!!!!!
                print("\n--- MyGO!!!!! ---")
                print("36. 高松灯   (36001-37000)")
                print("37. 千早爱音 (37001-38000)")
                print("38. 要乐奈   (38001-39000)")
                print("39. 长崎素世 (39001-40000)")
                print("40. 椎名立希 (40001-40999)")
                
                print("\n请输入人物编号，支持以下格式：")
                print("- 单个编号：1")
                print("- 多个编号：1,2,3 或 1、2、3 或 1 2 3")
                print("- 范围编号：1-3")
                
                member_choice = input("\n请选择要下载的人物卡面: ").strip()
                member_ids = parse_selection(member_choice)
                
                # 验证选择的ID是否有效
                valid_member_ids = [id for id in member_ids if get_character_info(id)]
                
                if not valid_member_ids:
                    print("\n⚠️ 错误：未选择有效的人物，程序退出")
                    return
                
                # 显示选中的角色信息
                show_selected_characters(valid_member_ids)
                
                # 计算总卡片数量
                total_cards = sum(
                    get_character_info(id)["range"][1] - get_character_info(id)["range"][0] + 1
                    for id in valid_member_ids
                )
                
                print(f"\n总计选择了 {len(valid_member_ids)} 名角色，预计包含 {total_cards} 张卡面")
                confirm = input("\n确认下载这些角色的卡面吗？(y/n): ").lower().strip()
                if confirm != 'y':
                    print("已取消下载")
                    return
                
                # 获取下载范围
                start_id = min(get_character_info(id)["range"][0] for id in valid_member_ids)
                end_id = max(get_character_info(id)["range"][1] for id in valid_member_ids)
                
                # 更新member_ids为有效的ID列表
                member_ids = valid_member_ids
                
            else:  # choice == "3"
                print("\n=== ID范围选择 ===")
                print("可用ID范围: 1001-40999")
                print("请输入起始ID和结束ID")
                
                try:
                    start_id = int(input("起始ID: ").strip())
                    end_id = int(input("结束ID: ").strip())
                    
                    if not (1001 <= start_id <= 40999 and 1001 <= end_id <= 40999):
                        raise ValueError("ID必须在1001-40999范围内")
                    if end_id <= start_id:
                        raise ValueError("结束ID必须大于起始ID")
                    
                    print(f"\n选择的ID范围: {start_id}-{end_id}")
                    confirm = input("确认下载此范围的卡面？(y/n): ").lower().strip()
                    if confirm != 'y':
                        print("已取消下载")
                        return
                        
                except ValueError as e:
                    print(f"输入无效: {e}")
                    return
            
            # 修改保存目录的创建方式
            save_dir = os.path.join(
                get_application_path(),  # 使用程序所在目录
                "downloads",
                datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            
            # 确保downloads目录存在
            os.makedirs(os.path.dirname(save_dir), exist_ok=True)
            
            # 创建下载器实例
            scraper = BestdoriScraper(save_dir, start_id, end_id, selected_members=member_ids)
            
            # 设置下载速度
            try:
                speed = float(input("\n下载速度 (0.1-5.0，默认1.0): ").strip() or "1.0")
                scraper.download_speed = max(0.1, min(5.0, speed))
            except ValueError:
                print("速度设置无效，使用默认值1.0")
            
            print(f"\n=== 配置信息 ===")
            print(f"起始ID: {start_id}")
            print(f"结束ID: {end_id}")
            print(f"保存目录: {save_dir}")
            print(f"下载速度: {scraper.download_speed}x")
            
            try:
                scraper.run()
            except Exception as e:
                logging.error(f"程序异常退出: {e}")
            
            # 下载完成后的用户交互
            print("\n" + "="*50)
            print("当前下载任务已完成！")
            print("="*50)
            print("\n请选择下一步操作：")
            print("1. 继续下载新的卡面")
            print("2. 退出程序")
            
            while True:
                next_action = input("\n请输入选项 [1/2]: ").strip()
                if next_action == "1":
                    print("\n" + "="*50)
                    print("开始新的下载任务...")
                    print("="*50 + "\n")
                    break
                elif next_action == "2":
                    print("\n" + "="*50)
                    print("小哥，你可真是这个！")
                    print("="*50)
                    return
                else:
                    print("无效的选项，请重新输入")
            
        except Exception as e:
            logging.error(f"程序异常退出: {e}")
            print("\n程序发生错误，是否继续？(y/n): ")
            if input().lower().strip() != 'y':
                return
        finally:
            if not next_action == "2":  # 如果不是选择退出程序
                print("\n按回车键继续...")
                input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已手动终止")
    except Exception as e:
        print(f"\n程序发生错误: {e}")
    finally:
        print("\n按回车键退出...")
        input() 