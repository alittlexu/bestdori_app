# 启动指南

## 🚀 快速开始（根据您的环境选择）

### 📦 方式一：Python Embedded（推荐 - 无 Python 环境用户）

**适合：没有安装 Python 的用户**

1. 双击运行 `setup-python-embedded.bat`（首次运行，自动下载 Python）
2. 双击运行 `install-dependencies.bat`（安装依赖）
3. 双击运行 `run-embedded.bat`（启动应用）

> 📖 详细说明请查看 [README_EMBEDDED.md](README_EMBEDDED.md)

### 💻 方式二：本地 Python 环境（开发者）

**适合：已安装 Python 3.8+ 的用户**

#### 使用 Python 脚本（推荐）
```bash
python run.py
```

#### 使用批处理文件（Windows）
双击 `run.bat` 或在命令行运行：
```bash
run.bat
```

#### 直接运行主程序（开发模式）
```bash
python src/main.py
```

## 📋 说明

- **`run.py`**：项目根目录下的主启动脚本，推荐使用此方式启动
- **`run.bat`**：Windows 批处理启动脚本，自动设置编码并启动程序
- **`src/main.py`**：原始入口点，保留用于兼容性

所有启动方式最终都会启动相同的 GUI 应用程序。

## 🎯 选择建议

| 用户类型 | 推荐方式 | 原因 |
|---------|---------|------|
| 普通用户（无 Python） | Python Embedded | 无需安装，GUI 支持完整 |
| 开发者 | 本地 Python | 开发调试方便 |

## ⚙️ 环境要求

- **Python Embedded 方式**：无需任何环境，自动配置
- **本地 Python 方式**：需要 Python 3.8 或更高版本

