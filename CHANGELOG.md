# 更新日志

## [2.1.0] - 2025-11-03

### ✨ 新增功能

#### 1. 动态卡面视频下载功能
- 新增 `animation_episode_downloader` 模块，支持下载 BanG Dream! 动态卡面视频 (MP4格式)
- 支持按乐队、乐器、角色筛选下载
- 自动创建 `Bestdori/animation/乐队/角色/` 文件夹结构
- 优化遍历逻辑：连续3次查找为空即停止（适合动态卡面数量较少的特点）

#### 2. 统一的下载路径管理
- 新增配置管理器 (`config_manager.py`)，统一管理下载根路径
- 新增路径工具 (`path_utils.py`)，自动构建 `Bestdori/<类型>/` 文件夹结构
- 所有下载功能统一保存到 `<用户设置的根路径>/Bestdori/` 目录下
- 支持三种下载类型的自动分类：
  - `Bestdori/card/` - 卡面下载
  - `Bestdori/animation/` - 动态卡面下载
  - `Bestdori/voice/` - 语音下载

#### 3. 路径设置UI
- 所有下载页面新增路径设置区域
- 显示当前下载保存路径
- 一键设置下载根路径，配置自动保存

### 🔧 改进优化

#### 文件名处理优化
- 修复 Windows 文件系统非法字符问题（如 `Pastel*Palettes` 中的星号）
- 支持全角字符清理（`＊` → `_`）
- 所有下载功能统一使用 `sanitize_filename` 函数处理文件名

#### 语音下载功能优化
- 修复 aya 等角色无法下载的问题（`aya` 现在可以直接作为 short_key 使用）
- 为语音下载添加乐队文件夹结构（`voice/乐队/角色/角色_mp3/`）
- 优化下载逻辑：从开头连续失败直接跳过该角色

#### 下载逻辑优化
- 动态卡面下载：从开头连续3次失败即跳过该角色
- 卡面下载：保持原有逻辑（连续8次失败停止）
- 语音下载：从开头连续15次失败即跳过该角色

### 🐛 Bug修复

1. **修复 Pastel*Palettes 乐队文件夹创建失败问题**
   - 原因：星号 `*` 是 Windows 文件系统非法字符
   - 修复：统一文件名清理，将非法字符替换为下划线

2. **修复语音下载中 aya 等角色无法下载问题**
   - 原因：`characters.json` 中没有 `"aya"` 键，只有中文昵称
   - 修复：添加 short_key 回退逻辑，如果映射表找不到，直接检查是否为有效的 short_key

3. **修复语音下载缺少乐队文件夹问题**
   - 原因：语音下载器未创建乐队文件夹
   - 修复：在 `_ensure_save_dir` 中添加乐队文件夹创建逻辑

### 📁 文件变更

#### 新增文件
- `src/core/animation_episode/__init__.py`
- `src/core/animation_episode/animation_episode_downloader.py`
- `src/ui/pages/animation_episode_download_page.py`
- `src/utils/config_manager.py`
- `src/utils/path_utils.py`
- `ANIMATION_EPISODE_DOWNLOADER_README.md`
- `test_animation_downloader.py`

#### 修改文件
- `src/ui/main_window.py` - 添加动态卡面下载页面入口
- `src/ui/pages/card_download_page.py` - 添加路径设置UI，使用新的路径结构
- `src/ui/pages/animation_episode_download_page.py` - 新增完整页面
- `src/ui/pages/voice_download_page.py` - 添加路径设置UI，修复乐队文件夹创建
- `src/core/voice/voice_downloader.py` - 优化下载逻辑，添加乐队文件夹支持，修复 aya 下载问题
- `build.py` - 更新版本号到 2.1.0
- `version.txt` - 更新版本信息

### 📝 技术细节

#### 路径结构示例
```
<用户设置的根路径>/
└── Bestdori/
    ├── card/                    # 卡面下载
    │   ├── Poppin_Party/
    │   │   └── ksm/
    │   │       ├── 1001_normal.png
    │   │       └── 1001_trained.png
    │   └── Pastel_Palettes/
    │       └── aya/
    ├── animation/               # 动态卡面下载
    │   ├── Poppin_Party/
    │   │   └── ksm/
    │   │       └── mov001001.mp4
    │   └── Pastel_Palettes/
    │       └── aya/
    └── voice/                   # 语音下载
        ├── Poppin_Party/
        │   └── ksm/
        │       └── ksm_mp3/
        │           └── res001001.mp3
        └── Pastel_Palettes/
            └── aya/
                └── aya_mp3/
```

### 🔄 升级说明

从 v1.0.0 升级到 v2.1.0：
1. 首次使用需要设置下载根路径（任意下载页面的"设置路径"按钮）
2. 所有下载内容将统一保存到 `Bestdori` 文件夹下
3. 旧版本的下载文件不受影响，可以手动迁移到新的路径结构

---

## [1.0.0] - 2025-04-03

### 初始版本
- 卡面下载功能
- 语音下载功能
- 基础UI界面

