# 🚀 快速开始指南

欢迎使用 Bestdori 应用！本指南将帮助您快速选择并运行应用。

## 📋 两种运行方式对比

| 方式 | 适合人群 | 需要环境 | 难度 | GUI支持 |
|------|---------|---------|------|---------|
| **Python Embedded** ⭐ | 普通用户 | 无需安装 | ⭐ 简单 | ✅ 完整 |
| **本地 Python** | 开发者 | Python 3.8+ | ⭐ 简单 | ✅ 完整 |

## 🎯 推荐选择

### 如果您是普通用户（没有 Python 环境）

👉 **选择：Python Embedded 方式**

**三步启动：**
1. 双击 `setup-python-embedded.bat`（首次运行，自动下载 Python）
2. 双击 `install-dependencies.bat`（安装依赖，约 5-10 分钟）
3. 双击 `run-embedded.bat`（启动应用）

> 📖 详细说明：[README_EMBEDDED.md](README_EMBEDDED.md)

### 如果您是开发者（已安装 Python）

👉 **选择：本地 Python 方式**

**启动方式：**
```bash
# 方式1：使用批处理文件
run.bat

# 方式2：使用Python命令
python run.py
```

## ❓ 常见问题

### Q: 我应该选择哪种方式？

- **Windows 桌面用户（无 Python）**：推荐 Python Embedded（最简单，GUI 支持最好）
- **开发者（已安装 Python）**：推荐本地 Python（便于调试）

### Q: Python Embedded 和安装 Python 有什么区别？

- **Python Embedded**：便携式，只下载 Python 解释器（约 10MB），不安装到系统
- **系统 Python**：需要完整安装 Python（约 100MB+），修改系统环境

### Q: 可以同时使用多种方式吗？

可以！每种方式都是独立的，不会相互影响。

### Q: 哪种方式启动最快？

- **本地 Python**：最快（已安装环境）
- **Python Embedded**：中等（首次需下载，之后很快）

## 📚 更多文档

- [完整启动指南](README_START.md)
- [Python Embedded 详细说明](README_EMBEDDED.md)

## 💡 提示

- 首次运行任何方式都需要下载依赖，请确保网络连接正常
- 如果下载速度慢，可以尝试使用国内镜像源
- 遇到问题可以查看对应方式文档中的"常见问题"部分

