import os
import json
import time
import logging
import requests


def sanitize_filename(filename):
    """清理文件名中的非法字符（Windows文件系统）"""
    # Windows不允许的字符: < > : " / \ | ? * （包括全角和半角）
    invalid_chars = '<>:"/\\|?*'
    # 也替换全角字符
    fullwidth_chars = {
        '＜': '<',
        '＞': '>',
        '：': ':',
        '"': '"',
        '"': '"',
        '／': '/',
        '＼': '\\',
        '｜': '|',
        '？': '?',
        '＊': '*'  # 全角星号
    }
    # 先将全角字符转换为半角，然后再替换
    for full, half in fullwidth_chars.items():
        filename = filename.replace(full, half)
    # 替换半角非法字符
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # 移除首尾空格和点
    filename = filename.strip(' .')
    # 限制文件名长度（Windows路径限制）
    if len(filename) > 255:
        filename = filename[:255]
    return filename


class VoiceDownloader:
    """Bestdori 人物语音下载器（控制台调试版）。

    设计目标：
    - Mirror 卡面下载的核心做法：多服务器回退、快速探测、失败连续上限停止等。
    - 输入为角色昵称（见 `src/core/voice/characters.json`），解析出标准短名（如 tomori、kasumi）。
    - 支持简单的模式参数（占位：card/intro/...），便于后续扩展分类。
    - 提供进度/状态回调，便于接入 GUI 或控制台调试。
    """

    def __init__(self, save_root_dir=None):
        self.session = self._create_session()

        # 保存目录（默认到项目 downloads/voices）
        self.save_root_dir = save_root_dir or os.path.join(os.getcwd(), 'downloads', 'voices')
        os.makedirs(self.save_root_dir, exist_ok=True)

        # 固定 jp 服务器（包含最新资源）
        self.server = 'jp'
        # 可用 gacha 语音资源包类型
        self.gacha_rip_types = [
            'limitedspin_rip',
            'limited_rip',
            'operationspin_rip',
            'spin_rip',
        ]

        # 日志
        self.logger = logging.getLogger('VoiceDownloader')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(logging.StreamHandler())

        # 角色昵称映射
        self.characters_map = self._load_characters_map()
        self.character_ranges = self._load_character_ranges()
        # 角色到乐队的映射 (short_key -> band_name)
        self.character_to_band = self._load_character_to_band()

    def _create_session(self):
        session = requests.Session()
        common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://bestdori.com/info/cards'
        }
        session.headers.update(common_headers)
        try:
            session.get('https://bestdori.com', timeout=10)
            session.get('https://bestdori.com/info/cards', timeout=10)
        except Exception:
            pass
        return session

    def _load_characters_map(self):
        """加载 `src/core/voice/characters.json` 并构建昵称->短名(short_key) 解析。
        JSON 格式形如："tomorin": ["高松 燈", "燈", "tomori", "MyGO!!!!!"]
        其中 index 2 位置为我们需要的 short_key。
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/core
        path = os.path.join(base_dir, 'voice', 'characters.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.logger.error(f"无法加载角色映射 {path}: {e}")
            return {}

        nick_to_short = {}
        for k, v in data.items():
            if k.startswith('_'):
                continue
            # v 至少有 3 个元素，第三个为 short_key
            try:
                short_key = v[2]
                if isinstance(short_key, str) and short_key:
                    nick_to_short[k.lower()] = short_key
            except Exception:
                continue
        return nick_to_short

    def _load_character_ranges(self):
        """从根目录 `character_list.json` 读取各角色(按 nickname)的卡面ID范围。
        返回: { short_key(nickname): (start_id, end_id) }
        """
        # 当前文件: src/core/voice/voice_downloader.py
        # 上移 4 层: voice -> core -> src -> project_root
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
        path = os.path.join(project_root, 'character_list.json')
        mapping = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for group in data.get('groups', []):
                for member in group.get('members', []):
                    short = (member.get('nickname') or '').strip()
                    r = member.get('id_range') or {}
                    start_id = r.get('start')
                    end_id = r.get('end')
                    if short and isinstance(start_id, int) and isinstance(end_id, int):
                        mapping[short] = (start_id, end_id)
        except Exception as e:
            self.logger.error(f"无法加载角色范围 {path}: {e}")
        return mapping

    def _load_character_to_band(self):
        """从 `characters.json` 加载角色到乐队的映射。
        返回: { short_key: band_name }
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/core
        path = os.path.join(base_dir, 'voice', 'characters.json')
        mapping = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k, v in data.items():
                if k.startswith('_'):
                    continue
                # v 格式: [全名, 短名, short_key, 乐队名, ...]
                try:
                    short_key = v[2] if len(v) > 2 else None
                    band_name = v[3] if len(v) > 3 else None
                    if short_key and band_name:
                        mapping[short_key] = band_name
                except Exception:
                    continue
        except Exception as e:
            self.logger.error(f"无法加载角色乐队映射 {path}: {e}")
        return mapping

    def _resolve_nicknames(self, nicknames):
        """将输入昵称列表解析为 short_key 列表（去重、保持顺序）。"""
        resolved = []
        seen = set()
        for raw in nicknames or []:
            key = (raw or '').strip().lower()
            if not key:
                continue
            
            # 先尝试从映射表查找
            short = self.characters_map.get(key)
            
            # 如果映射表中找不到，检查是否本身就是 short_key
            # 即：如果输入的就是 short_key（如 "aya"），检查它是否在 character_ranges 中
            if not short:
                # 检查 key 是否就是一个有效的 short_key
                if key in self.character_ranges:
                    short = key
                    self.logger.debug(f"昵称 '{raw}' 直接作为 short_key 使用")
                else:
                    self.logger.warning(f"无法解析昵称: '{raw}' (key: '{key}')")
                    continue
            
            if short and short not in seen:
                seen.add(short)
                resolved.append(short)
                self.logger.debug(f"昵称 '{raw}' 解析为 short_key: '{short}'")
        
        return resolved

    def _ensure_save_dir(self, short_key):
        """确保保存目录存在，创建结构：downloads/voices/<band_name>/<short>/<short>_mp3"""
        # 获取角色所属乐队
        band_name = self.character_to_band.get(short_key, 'その他')
        if not band_name:
            band_name = 'その他'
            self.logger.warning(f"角色 {short_key} 未找到乐队信息，使用默认乐队：{band_name}")
        
        # 清理乐队名称中的非法字符
        sanitized_band_name = sanitize_filename(band_name)
        
        # 创建目录结构：<save_root>/<band_name>/<short_key>/<short_key>_mp3
        band_dir = os.path.join(self.save_root_dir, sanitized_band_name)
        char_dir = os.path.join(band_dir, short_key)
        target = os.path.join(char_dir, f"{short_key}_mp3")
        
        try:
            os.makedirs(target, exist_ok=True)
            self.logger.debug(f"创建保存目录: {target}")
        except Exception as e:
            self.logger.error(f"创建保存目录失败 {target}: {e}")
            raise
        
        return target

    def _candidate_voice_urls_from_res(self, server, res_id):
        """根据卡面资源ID(resXXXXXX)构造语音URL候选（gacha 下 rip 类型组合），统一以 .mp3 结尾。"""
        base = f"https://bestdori.com/assets/{server}"
        res = f"res{str(res_id).zfill(6)}"
        return [f"{base}/sound/voice/gacha/{rip}/{res}.mp3" for rip in self.gacha_rip_types]

    # 已弃用：animation_episode 闪限 MP4 遍历，因影响速度而移除

    def _download_binary(self, url, save_path, min_size=512, timeout=15):
        try:
            headers = {
                'Accept': 'audio/mpeg,audio/*;q=0.9,*/*;q=0.8',
                'Referer': 'https://bestdori.com/info/cards'
            }
            resp = self.session.get(url, headers=headers, timeout=timeout, stream=False, allow_redirects=True)
            if resp.status_code != 200:
                return False
            content_type = resp.headers.get('content-type', '')
            data = resp.content or b''
            if len(data) < min_size:
                return False
            # 基础 MP3 魔数校验：ID3 或通用帧同步 (0xFFE*)；若服务端明确返回 audio/* 也放行
            valid_magic = False
            if content_type.startswith('audio/'):
                valid_magic = True
            elif len(data) >= 3 and data[:3] == b'ID3':
                valid_magic = True
            elif len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
                valid_magic = True
            if not valid_magic:
                # 很可能是 HTML/错误页，跳过保存
                return False
            with open(save_path, 'wb') as f:
                f.write(data)
            return True
        except Exception:
            return False

    def _quick_head_ok(self, url, retries=2):
        """对语音 URL 做快速 HEAD 探测，考虑网络波动做少量重试。"""
        try:
            for _ in range(max(1, retries)):
                r = self.session.head(url, timeout=4, allow_redirects=True)
                if r.status_code == 200:
                    return True
                time.sleep(0.2)
        except Exception:
            return False
        return False

    def _try_download_voice_for_res(self, short_key, res_id, status_callback=None):
        """对单个卡面资源ID尝试下载对应语音或动画集 MP4：
        1) 先按 gacha rip 类型尝试 mp3
        2) 若均未命中，再尝试 animation_episode 的 mp4
        命中即保存到同目录
        """
        server = self.server
        filename = f"res{str(res_id).zfill(6)}.mp3"
        save_dir = self._ensure_save_dir(short_key)
        save_path = os.path.join(save_dir, filename)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
            return True
        # 1) gacha mp3
        urls = self._candidate_voice_urls_from_res(server, res_id)
        for url in urls:
            if not url.endswith('.mp3'):
                continue
            if status_callback:
                status_callback(f"尝试 {os.path.basename(save_path)} @ {server}")
            if not self._quick_head_ok(url, retries=3):
                url_ts = url + ("?t=" + str(int(time.time()*1000)))
                if not self._quick_head_ok(url_ts, retries=2):
                    continue
                url = url_ts
            if self._download_binary(url, save_path, min_size=512):
                if status_callback:
                    status_callback(f"已保存: {save_path}")
                return True

        # 不再尝试 animation_episode mp4（闪限卡）
        return False

    def download_by_characters(self,
                               nicknames,
                               mode='card',
                               to_wav=False,
                               start_index=1,
                               end_index=200,
                               max_consecutive_miss=15,
                               status_callback=None,
                               progress_callback=None):
        """按角色昵称列表批量下载语音。

        参数说明：
        - nicknames: 昵称或别名列表（将解析为短名 short_key）
        - mode: 预留分类占位（当前不影响 URL，后续可扩展）
        - to_wav: 预留转换开关（暂不实现）
        - start_index/end_index: 语音文件猜测范围
        - max_consecutive_miss: 连续未命中阈值（达到则视为该角色语音基本遍历完成）
        - status_callback/progress_callback: 状态/进度回调
        """
        short_keys = self._resolve_nicknames(nicknames)
        stats = {
            'characters': short_keys,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }

        # 预估任务量：按角色范围大小粗略估算
        estimated = 0
        for short in short_keys:
            r = self.character_ranges.get(short)
            if r:
                estimated += max(0, r[1] - r[0] + 1)
        total_tasks = max(1, estimated)
        finished = 0

        for short in short_keys:
            rng = self.character_ranges.get(short)
            if not rng:
                if status_callback:
                    status_callback(f"未找到角色范围: {short}，跳过该角色")
                self.logger.warning(f"未找到角色 {short} 的范围信息")
                stats['skipped'] += 1
                continue
            start_id, end_id = rng
            misses = 0
            found_any = False  # 记录是否找到过任何语音文件
            if status_callback:
                status_callback(f"开始下载角色语音(卡面派生): {short} | 范围 {start_id}-{end_id}")
            self.logger.info(f"开始下载角色 {short}，范围: {start_id}-{end_id}")
            
            # 优化：如果从开头就连续失败，提前结束（类似 animation_episode_downloader 的逻辑）
            for res_id in range(start_id, end_id + 1):
                ok = self._try_download_voice_for_res(short, res_id, status_callback=status_callback)
                finished += 1
                if progress_callback:
                    progress_callback(finished * 100.0 / total_tasks)
                if ok:
                    stats['downloaded'] += 1
                    misses = 0
                    found_any = True
                    self.logger.info(f"角色 {short} 下载成功: res{str(res_id).zfill(6)}.mp3")
                else:
                    misses += 1
                    # 如果从开头就连续失败 max_consecutive_miss 次，判定该角色可能没有语音文件
                    if not found_any and misses >= max_consecutive_miss:
                        if status_callback:
                            status_callback(f"{short}: 从开头连续未命中 {misses} 次，判定该角色可能没有语音文件，跳过后续扫描")
                        self.logger.warning(f"角色 {short} 从开头连续失败 {misses} 次，跳过该角色")
                        break
                    # 如果找到过文件，然后又连续失败 max_consecutive_miss 次，判定为下载完成
                    elif found_any and misses >= max_consecutive_miss:
                        if status_callback:
                            status_callback(f"{short}: 已找到语音文件，且连续未命中 {misses} 次，判定为下载完成")
                        self.logger.info(f"角色 {short} 下载完成，连续失败 {misses} 次后停止")
                        break
                time.sleep(0.08)
            
            if not found_any:
                self.logger.warning(f"角色 {short} 未找到任何语音文件")

        if status_callback:
            status_callback("语音下载流程结束。")
        return stats


