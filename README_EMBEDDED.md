# Python Embedded 运行方式

本方式适用于**没有 Python 环境**的用户，会自动下载并配置便携式 Python 环境，无需手动安装 Python。

## 特点

- ✅ **无需安装 Python**：自动下载 Python Embedded 版本
- ✅ **便携式**：所有文件都在项目目录中，不污染系统
- ✅ **GUI 支持完整**：与原生 Python 环境体验一致
- ✅ **依赖自动安装**：一键安装所有必需的包

## 快速开始

### 步骤 1：配置 Python Embedded 环境

双击运行 `setup-python-embedded.bat`

脚本会自动：
1. 下载 Python Embedded 3.11.9（约 10MB）
2. 解压到 `python_embedded` 目录
3. 配置 pip 和包管理

**注意**：首次运行需要网络连接，下载时间取决于网速（通常 1-3 分钟）

### 步骤 2：安装依赖包

双击运行 `install-dependencies.bat`

脚本会自动：
1. 安装 pip（如果未安装）
2. 安装 `requirements.txt` 中的所有依赖包

**注意**：首次安装可能需要 5-10 分钟，取决于网络速度和依赖数量

### 步骤 3：启动应用

双击运行 `run-embedded.bat`

应用会自动启动！

## 目录结构

配置完成后，项目目录会包含：

```
bestdori_app/
├── python_embedded/          # Python Embedded 环境（自动创建）
│   ├── python.exe            # Python 解释器
│   ├── Scripts/              # pip 等工具
│   └── site-packages/        # 安装的依赖包
├── setup-python-embedded.bat # 环境配置脚本
├── install-dependencies.bat  # 依赖安装脚本
└── run-embedded.bat          # 启动脚本
```

## 使用国内镜像加速（可选）

如果下载速度慢，可以修改 `install-dependencies.bat`，在 pip install 命令中添加镜像源：

```batch
python_embedded\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-warn-script-location -r requirements.txt
```

## 常见问题

### Q: 下载 Python Embedded 失败？
A: 
1. 检查网络连接
2. 如果无法访问 python.org，可以手动下载：
   - 访问 https://www.python.org/downloads/windows/
   - 下载 "Windows embeddable package (64-bit)"
   - 解压到 `python_embedded` 目录
   - 重新运行 `setup-python-embedded.bat`

### Q: 依赖安装失败？
A:
1. 检查网络连接
2. 尝试使用国内镜像源（见上方说明）
3. 确保有足够的磁盘空间（至少 500MB）

### Q: 如何更新依赖？
A: 直接运行 `install-dependencies.bat`，会自动更新所有依赖

### Q: 如何删除 Python Embedded 环境？
A: 直接删除 `python_embedded` 文件夹即可

### Q: 可以多个项目共享同一个 Embedded Python 吗？
A: 可以，但建议每个项目使用独立的 Embedded Python，避免依赖冲突

## 优势对比

| 特性 | Python Embedded | 系统 Python |
|------|----------------|-------------|
| 无需安装 Python | ✅ | ❌ |
| GUI 支持 | ✅ 完整 | ✅ 完整 |
| 便携性 | ✅ 高 | ❌ 低 |
| 启动速度 | ✅ 快 | ✅ 快 |
| 资源占用 | ✅ 低 | ✅ 低 |
| 推荐场景 | Windows 桌面用户 | 开发者 |

## 重新安装

如果需要重新开始：

1. 删除 `python_embedded` 文件夹
2. 重新运行 `setup-python-embedded.bat`

所有配置和下载的文件都会保存在项目目录中，不会影响系统其他部分。

