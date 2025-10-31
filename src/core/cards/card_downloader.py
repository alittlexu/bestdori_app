import os
import logging
import requests
from PIL import Image
from io import BytesIO


class BestdoriDownloader:
    """Bestdori卡面下载器（抽离至核心模块）。"""

    def __init__(self, save_dir=None):
        self.save_dir = save_dir or os.getcwd()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.servers = ['jp', 'en', 'tw', 'cn', 'kr']
        self.stats = {
            "complete": 0,     # 完整下载（普通+特训）
            "normal_only": 0,  # 仅普通版本
            "trained_only": 0, # 仅特训版本
            "failed": 0,       # 下载失败
            "nonexistent": []  # 不存在的ID列表
        }

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def check_card_exists(self, card_id):
        """检查卡片是否存在，并验证图片分辨率"""
        exists = {'normal': False, 'trained': False}
        server_used = None

        # 首先尝试检查normal形态（只检查一次）
        normal_url = f"https://bestdori.com/assets/jp/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_normal.png"
        try:
            response = self.session.head(normal_url, timeout=3)
            if response.status_code == 200 and ('content-length' not in response.headers or int(response.headers.get('content-length', '0')) > 100):
                # 获取完整图片内容并检查分辨率
                response = self.session.get(normal_url, timeout=5)
                if response.status_code == 200 and len(response.content) > 1024:
                    try:
                        img = Image.open(BytesIO(response.content))
                        width, height = img.size
                        if width == 1334 and height == 1002:
                            exists['normal'] = True
                            server_used = 'jp'
                            logging.info(f"卡片 {card_id} normal形态卡面验证成功 (分辨率: {width}x{height})")
                        else:
                            logging.warning(f"卡片 {card_id} normal形态卡面验证失败 (分辨率: {width}x{height})")
                    except Exception as e:
                        logging.warning(f"卡片 {card_id} normal形态卡面验证失败: {str(e)}")
                else:
                    logging.debug(f"卡片 {card_id} normal形态卡面验证失败: 状态码 {response.status_code} 或内容长度不足")
            else:
                logging.debug(f"卡片 {card_id} normal形态卡面不存在")
        except Exception as e:
            logging.debug(f"检查卡片 {card_id} normal形态出错: {str(e)}")

        # 如果normal形态不存在，检查trained形态（只检查一次）
        if not exists['normal']:
            logging.info(f"卡片 {card_id} normal形态不存在，检查trained形态")

            trained_url = f"https://bestdori.com/assets/jp/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_after_training.png"
            try:
                response = self.session.head(trained_url, timeout=3)
                if response.status_code == 200 and ('content-length' not in response.headers or int(response.headers.get('content-length', '0')) > 100):
                    response = self.session.get(trained_url, timeout=5)
                    if response.status_code == 200 and len(response.content) > 1024:
                        try:
                            img = Image.open(BytesIO(response.content))
                            width, height = img.size
                            if width == 1334 and height == 1002:
                                exists['trained'] = True
                                server_used = 'jp'
                                logging.info(f"卡片 {card_id} trained形态卡面验证成功 (分辨率: {width}x{height})")
                            else:
                                logging.warning(f"卡片 {card_id} trained形态卡面验证失败 (分辨率: {width}x{height})")
                        except Exception as e:
                            logging.warning(f"卡片 {card_id} trained形态卡面验证失败: {str(e)}")
                    else:
                        logging.warning(f"卡片 {card_id} trained形态卡面验证失败: 状态码 {response.status_code} 或内容长度不足")
                else:
                    logging.debug(f"卡片 {card_id} trained形态卡面不存在")
            except Exception as e:
                logging.debug(f"检查卡片 {card_id} trained形态出错: {str(e)}")
        else:
            # 如果normal形态存在，检查trained形态（只检查一次）
            trained_url = f"https://bestdori.com/assets/jp/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_after_training.png"
            try:
                response = self.session.head(trained_url, timeout=3)
                if response.status_code == 200 and ('content-length' not in response.headers or int(response.headers.get('content-length', '0')) > 100):
                    response = self.session.get(trained_url, timeout=5)
                    if response.status_code == 200 and len(response.content) > 1024:
                        try:
                            img = Image.open(BytesIO(response.content))
                            width, height = img.size
                            if width == 1334 and height == 1002:
                                exists['trained'] = True
                                logging.info(f"卡片 {card_id} trained形态卡面验证成功 (分辨率: {width}x{height})")
                            else:
                                logging.warning(f"卡片 {card_id} trained形态卡面验证失败 (分辨率: {width}x{height})")
                        except Exception as e:
                            logging.warning(f"卡片 {card_id} trained形态卡面验证失败: {str(e)}")
                    else:
                        logging.debug(f"卡片 {card_id} trained形态卡面不存在")
                else:
                    logging.debug(f"卡片 {card_id} trained形态卡面不存在")
            except Exception as e:
                logging.debug(f"检查卡片 {card_id} trained形态出错: {str(e)}")

        return exists, server_used

    def download_card(self, card_id, server=None):
        """下载卡片图片"""
        result = {'normal': False, 'trained': False}

        # 如果没有指定服务器，先检查卡片是否存在
        if not server:
            exists, server = self.check_card_exists(card_id)
            if not exists['normal'] and not exists['trained']:
                logging.info(f"卡片 {card_id} 在所有服务器上都不存在")
                return result

        if not server:
            logging.info(f"卡片 {card_id} 没有找到可用的服务器")
            return result

        # 下载普通版本
        normal_url = f"https://bestdori.com/assets/{server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_normal.png"
        normal_path = os.path.join(self.save_dir, f"{card_id}_normal.png")

        try:
            response = self.session.get(normal_url, timeout=10)
            if response.status_code == 200 and len(response.content) > 1024:
                try:
                    # 验证图片分辨率
                    img = Image.open(BytesIO(response.content))
                    width, height = img.size
                    if width == 1334 and height == 1002:
                        # 分辨率正确，保存图片
                        with open(normal_path, 'wb') as f:
                            f.write(response.content)
                        result['normal'] = True
                        logging.info(f"卡片 {card_id} normal形态下载成功: {normal_path} (分辨率: {width}x{height})")
                    else:
                        logging.warning(f"卡片 {card_id} normal形态分辨率不符 (分辨率: {width}x{height})，跳过下载")
                except Exception as e:
                    logging.warning(f"卡片 {card_id} normal形态验证失败: {str(e)}")
            else:
                logging.warning(f"卡片 {card_id} normal形态下载失败: 状态码 {response.status_code} 或内容长度不足")
        except Exception as e:
            logging.error(f"下载卡片 {card_id} normal形态失败: {str(e)}")

        # 下载特训版本
        trained_url = f"https://bestdori.com/assets/{server}/characters/resourceset/res{str(card_id).zfill(6)}_rip/card_after_training.png"
        trained_path = os.path.join(self.save_dir, f"{card_id}_trained.png")

        try:
            response = self.session.get(trained_url, timeout=10)
            if response.status_code == 200 and len(response.content) > 1024:
                try:
                    # 验证图片分辨率
                    img = Image.open(BytesIO(response.content))
                    width, height = img.size
                    if width == 1334 and height == 1002:
                        # 分辨率正确，保存图片
                        with open(trained_path, 'wb') as f:
                            f.write(response.content)
                        result['trained'] = True
                        logging.info(f"卡片 {card_id} trained形态下载成功: {trained_path} (分辨率: {width}x{height})")
                    else:
                        logging.warning(f"卡片 {card_id} trained形态分辨率不符 (分辨率: {width}x{height})，跳过下载")
                except Exception as e:
                    logging.warning(f"卡片 {card_id} trained形态验证失败: {str(e)}")
            else:
                logging.warning(f"卡片 {card_id} trained形态下载失败: 状态码 {response.status_code} 或内容长度不足")
        except Exception as e:
            logging.error(f"下载卡片 {card_id} trained形态失败: {str(e)}")

        return result

    def download_character_cards(self, character_id_start, character_id_end=None, callback=None):
        """下载指定角色范围的卡片"""
        if character_id_end is None:
            character_id_end = character_id_start + 999

        total_checked = 0
        consecutive_nonexistent = 0  # 连续不存在的卡片计数
        max_consecutive_nonexistent = 8  # 连续8次无新卡片则视为下载完成
        found_any_card = False  # 是否找到过任何卡片

        logging.info(f"开始下载角色卡片，ID范围: {character_id_start} - {character_id_end}")

        for card_id in range(character_id_start, character_id_end + 1):
            # 检查卡片是否存在
            exists, server = self.check_card_exists(card_id)

            if not exists['normal'] and not exists['trained']:
                # 卡片不存在，增加连续计数
                consecutive_nonexistent += 1
                self.stats["nonexistent"].append(card_id)
                logging.info(f"卡片 {card_id} 不存在，连续计数: {consecutive_nonexistent}")

                # 如果找到过卡片，并且连续8次没有找到卡片，判定为已下载完成
                if found_any_card and consecutive_nonexistent >= max_consecutive_nonexistent:
                    logging.info(f"已找到卡片，且连续{max_consecutive_nonexistent}次未找到新卡片，判定为下载完成")
                    break

                continue

            # 找到了卡片，记录状态并重置连续计数
            found_any_card = True
            consecutive_nonexistent = 0
            logging.info(f"找到卡片 {card_id}，重置连续不存在计数")

            # 下载找到的卡片
            result = self.download_card(card_id, server)

            # 更新统计信息
            if result['normal'] and result['trained']:
                self.stats["complete"] += 1
                logging.info(f"卡片 {card_id} 完整下载成功")
            elif result['normal']:
                self.stats["normal_only"] += 1
                logging.info(f"卡片 {card_id} 仅normal形态下载成功")
            elif result['trained']:
                self.stats["trained_only"] += 1
                logging.info(f"卡片 {card_id} 仅trained形态下载成功")
            else:
                self.stats["failed"] += 1
                logging.info(f"卡片 {card_id} 下载失败")

            total_checked += 1

            # 回调通知进度
            if callback:
                callback(card_id, total_checked, character_id_end - character_id_start + 1, self.stats)

        # 如果完全没有找到卡片
        if not found_any_card:
            logging.warning(f"ID范围 {character_id_start} - {character_id_end} 内未找到任何卡片")

        return self.stats


