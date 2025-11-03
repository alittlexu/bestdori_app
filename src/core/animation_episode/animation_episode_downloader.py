import os
import logging
import requests


class AnimationEpisodeDownloader:
    """Bestdori动态卡面视频下载器"""

    def __init__(self, save_dir=None):
        self.save_dir = save_dir or os.getcwd()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.servers = ['jp', 'en', 'tw', 'cn', 'kr']
        self.stats = {
            "downloaded": 0,      # 成功下载的视频数
            "failed": 0,          # 下载失败
            "nonexistent": []     # 不存在的ID列表
        }

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def check_video_exists(self, video_id):
        """检查动态卡面视频是否存在"""
        exists = False
        server_used = None

        # 构建视频URL - 参考用户提供的URL格式
        # https://bestdori.com/assets/cn/movie/animation_episode/mov001001_rip/mov001001.mp4
        video_url = f"https://bestdori.com/assets/cn/movie/animation_episode/mov{str(video_id).zfill(6)}_rip/mov{str(video_id).zfill(6)}.mp4"
        
        try:
            response = self.session.head(video_url, timeout=5)
            if response.status_code == 200:
                content_length = int(response.headers.get('content-length', 0))
                # 视频文件应该比较大，至少要大于10KB
                if content_length > 10240:
                    exists = True
                    server_used = 'cn'
                    logging.info(f"动态卡面视频 {video_id} 存在 (大小: {content_length} bytes)")
                else:
                    logging.debug(f"动态卡面视频 {video_id} 文件过小: {content_length} bytes")
            else:
                logging.debug(f"动态卡面视频 {video_id} 不存在 (状态码: {response.status_code})")
        except Exception as e:
            logging.debug(f"检查动态卡面视频 {video_id} 出错: {str(e)}")

        return exists, server_used

    def download_video(self, video_id, server=None):
        """下载动态卡面视频"""
        result = False

        # 如果没有指定服务器，先检查视频是否存在
        if not server:
            exists, server = self.check_video_exists(video_id)
            if not exists:
                logging.info(f"动态卡面视频 {video_id} 不存在")
                return result

        if not server:
            logging.info(f"动态卡面视频 {video_id} 没有找到可用的服务器")
            return result

        # 下载视频
        video_url = f"https://bestdori.com/assets/{server}/movie/animation_episode/mov{str(video_id).zfill(6)}_rip/mov{str(video_id).zfill(6)}.mp4"
        video_path = os.path.join(self.save_dir, f"mov{str(video_id).zfill(6)}.mp4")

        try:
            response = self.session.get(video_url, timeout=30, stream=True)
            if response.status_code == 200:
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                
                # 检查文件大小是否合理（至少10KB）
                if total_size < 10240:
                    logging.warning(f"动态卡面视频 {video_id} 文件过小: {total_size} bytes，跳过下载")
                    return result
                
                # 保存视频文件
                with open(video_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                result = True
                logging.info(f"动态卡面视频 {video_id} 下载成功: {video_path} (大小: {downloaded} bytes)")
            else:
                logging.warning(f"动态卡面视频 {video_id} 下载失败: 状态码 {response.status_code}")
        except Exception as e:
            logging.error(f"下载动态卡面视频 {video_id} 失败: {str(e)}")

        return result

    def download_character_videos(self, character_id_start, character_id_end=None, callback=None):
        """下载指定角色范围的动态卡面视频"""
        if character_id_end is None:
            character_id_end = character_id_start + 999

        total_checked = 0
        consecutive_nonexistent = 0  # 连续不存在的视频计数
        max_consecutive_nonexistent = 3  # 连续3次无新视频则视为下载完成（用户要求）
        found_any_video = False  # 是否找到过任何视频

        logging.info(f"开始下载角色动态卡面视频，ID范围: {character_id_start} - {character_id_end}")

        for video_id in range(character_id_start, character_id_end + 1):
            # 检查视频是否存在
            exists, server = self.check_video_exists(video_id)

            if not exists:
                # 视频不存在，增加连续计数
                consecutive_nonexistent += 1
                self.stats["nonexistent"].append(video_id)
                logging.info(f"动态卡面视频 {video_id} 不存在，连续计数: {consecutive_nonexistent}")

                # 优化：如果从开头就连续3次查找失败，直接判定该人物不存在动态卡面，跳过
                if not found_any_video and consecutive_nonexistent >= max_consecutive_nonexistent:
                    logging.info(f"从开头连续{max_consecutive_nonexistent}次未找到视频，判定该人物不存在动态卡面，跳过后续查找")
                    break

                # 如果找到过视频，并且连续3次没有找到视频，判定为已下载完成
                if found_any_video and consecutive_nonexistent >= max_consecutive_nonexistent:
                    logging.info(f"已找到视频，且连续{max_consecutive_nonexistent}次未找到新视频，判定为下载完成")
                    break

                continue

            # 找到了视频，记录状态并重置连续计数
            found_any_video = True
            consecutive_nonexistent = 0
            logging.info(f"找到动态卡面视频 {video_id}，重置连续不存在计数")

            # 下载找到的视频
            result = self.download_video(video_id, server)

            # 更新统计信息
            if result:
                self.stats["downloaded"] += 1
                logging.info(f"动态卡面视频 {video_id} 下载成功")
            else:
                self.stats["failed"] += 1
                logging.info(f"动态卡面视频 {video_id} 下载失败")

            total_checked += 1

            # 回调通知进度
            if callback:
                callback(video_id, total_checked, character_id_end - character_id_start + 1, self.stats)

        # 如果完全没有找到视频
        if not found_any_video:
            logging.warning(f"ID范围 {character_id_start} - {character_id_end} 内未找到任何动态卡面视频，该人物可能没有动态卡面资源")

        return self.stats

