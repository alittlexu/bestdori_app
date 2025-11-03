# Animation Episode Downloader 功能说明

## 概述

animation_episode_downloader 是一个用于下载 Bestdori 网站上 BanG Dream! 游戏动态卡面视频（mp4格式）的功能模块。该功能完全参考了现有的 card_downloader 实现，提供了类似的搜索、下载和筛选功能。

## 功能特点

### 1. 核心下载功能
- **视频格式**: MP4
- **URL模式**: `https://bestdori.com/assets/cn/movie/animation_episode/mov{ID}_rip/mov{ID}.mp4`
- **ID格式**: 6位数字，例如 `001001`
- **遍历策略**: 连续3次查找为空则视为该人物动态卡面已搜索结束（区别于卡面下载器的8次）

### 2. 筛选功能
支持以下筛选条件：
- **按乐队筛选**: 9个乐队（Poppin'Party、Afterglow等）
- **按乐器筛选**: 7种乐器（吉他、贝斯、鼓、键盘、主唱、DJ、小提琴）
- **按角色筛选**: 40个角色
- 支持多选和"全部"选项

### 3. 文件管理
- 自动创建乐队文件夹结构
- 自动创建角色子文件夹
- 示例：`Poppin'Party/ksm/mov001001.mp4`

### 4. UI功能
- 实时进度显示
- 详细的下载日志
- 下载统计信息
- 支持停止/刷新操作

## 文件结构

```
bestdori_app/
├── src/
│   ├── core/
│   │   └── animation_episode/
│   │       ├── __init__.py
│   │       └── animation_episode_downloader.py    # 核心下载器类
│   └── ui/
│       ├── main_window.py                         # 主窗口（已更新）
│       └── pages/
│           └── animation_episode_download_page.py # UI页面
└── test_animation_downloader.py                   # 测试脚本
```

## 核心类说明

### AnimationEpisodeDownloader

位置：`src/core/animation_episode/animation_episode_downloader.py`

#### 主要方法：

1. **`check_video_exists(video_id)`**
   - 检查指定ID的动态卡面视频是否存在
   - 返回：(exists: bool, server: str)

2. **`download_video(video_id, server=None)`**
   - 下载单个动态卡面视频
   - 返回：bool（下载是否成功）

3. **`download_character_videos(character_id_start, character_id_end=None, callback=None)`**
   - 批量下载角色的动态卡面视频
   - 实现了连续3次查找为空的停止逻辑
   - 支持进度回调

#### 统计信息：

```python
stats = {
    "downloaded": 0,      # 成功下载的视频数
    "failed": 0,          # 下载失败
    "nonexistent": []     # 不存在的ID列表
}
```

### AnimationEpisodeDownloadPage

位置：`src/ui/pages/animation_episode_download_page.py`

完整的PyQt6界面，包含：
- 乐队/乐器/角色筛选下拉菜单
- 下载/刷新/停止按钮
- 进度条和状态显示
- 下载日志区域
- 使用说明和关于对话框

## 使用方法

### 1. 通过UI使用

1. 启动应用程序
2. 点击工具栏 "卡面获取" → "下载动态卡面"
3. 选择乐队、乐器或角色（支持多选）
4. 点击"下载"按钮
5. 选择保存目录
6. 等待下载完成

### 2. 通过代码使用

```python
from src.core.animation_episode.animation_episode_downloader import AnimationEpisodeDownloader

# 创建下载器实例
downloader = AnimationEpisodeDownloader(save_dir="./downloads")

# 下载单个视频
result = downloader.download_video(1001)

# 批量下载（带进度回调）
def progress_callback(video_id, current, total, stats):
    print(f"正在下载: {video_id}, 进度: {current}/{total}")

stats = downloader.download_character_videos(
    1000,  # 起始ID（户山香澄）
    1999,  # 结束ID
    callback=progress_callback
)

print(f"下载完成，成功: {stats['downloaded']}, 失败: {stats['failed']}")
```

## 测试

运行测试脚本：

```bash
python test_animation_downloader.py
```

测试脚本包含：
- 视频存在性检查测试
- 单个视频下载测试（已注释）
- 批量下载测试（已注释）

**注意**: 默认只执行存在性检查测试，下载测试需手动取消注释。

## 角色ID映射

动态卡面视频ID与角色ID的映射关系：

| 角色ID | 角色名 | 视频ID范围 | 昵称 |
|--------|--------|-----------|------|
| 1 | 戸山香澄 | 1000-1999 | ksm |
| 2 | 花園たえ | 2000-2999 | tae |
| 3 | 牛込りみ | 3000-3999 | rimi |
| ... | ... | ... | ... |
| 36 | 高松燈 | 36001-36999 | tomorin |
| 37 | 千早愛音 | 37001-37999 | ano |
| 38 | 要楽奈 | 38001-38999 | rana |
| 39 | 長崎そよ | 39001-39999 | soyo |
| 40 | 椎名立希 | 40001-40999 | taki |

## 与 card_downloader 的区别

| 特性 | card_downloader | animation_episode_downloader |
|------|-----------------|------------------------------|
| 下载内容 | 静态卡面图片(PNG) | 动态卡面视频(MP4) |
| 文件格式 | card_normal.png / card_after_training.png | mov{ID}.mp4 |
| URL模式 | .../resourceset/res{ID}_rip/... | .../animation_episode/mov{ID}_rip/... |
| 遍历停止条件 | 连续8次查找为空 | 连续3次查找为空 |
| 形态支持 | normal + trained | 单一视频 |
| 分辨率验证 | 1334x1002 | 文件大小 >10KB |

## 注意事项

1. **网络要求**: 
   - 视频文件较大，需要稳定的网络连接
   - 建议使用有线连接或稳定的WiFi

2. **存储空间**: 
   - 单个动态卡面视频通常在几MB到几十MB
   - 下载前请确保有足够的磁盘空间

3. **下载速度**: 
   - 受网络环境影响
   - 使用流式下载，支持大文件

4. **资源版权**: 
   - 所有资源版权归 BanG Dream! 及 Craft Egg/Bushiroad 所有
   - 仅供个人学习和欣赏使用

5. **遍历策略**: 
   - 由于动态卡面数量较少，连续3次查找为空即停止
   - 可以通过修改 `max_consecutive_nonexistent` 参数调整

## 错误处理

下载器包含完善的错误处理：
- 网络超时自动重试
- 文件大小验证
- 详细的日志记录
- 友好的错误提示

## 日志级别

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

可以通过修改 `level` 参数调整日志详细程度：
- `logging.DEBUG`: 详细调试信息
- `logging.INFO`: 常规信息（默认）
- `logging.WARNING`: 警告信息
- `logging.ERROR`: 错误信息

## 开发说明

### 添加新功能

如需添加新功能，建议参考以下文件：
1. 核心逻辑：`src/core/animation_episode/animation_episode_downloader.py`
2. UI界面：`src/ui/pages/animation_episode_download_page.py`
3. 主窗口集成：`src/ui/main_window.py`

### 自定义配置

可以通过修改以下参数自定义行为：
- `max_consecutive_nonexistent`: 连续查找为空的次数（默认3）
- 超时时间：`timeout` 参数（默认30秒）
- 分块大小：`chunk_size` 参数（默认8192字节）

## 版本信息

- 版本: 2.1.0
- 开发日期: 2025-11-03
- 基于: card_downloader v2.1.0

## 许可

本工具仅供学习交流使用，请勿用于商业用途。

