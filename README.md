# bestdori_app
# BanG Dream! 卡面下载工具

一个用于下载BanG Dream! 游戏卡面的桌面应用程序。

## 功能特点

- 支持按乐队、角色、乐器筛选卡面
- 支持按星级筛选卡面
- 支持下载普通卡面和觉醒卡面
- 自动按乐队和角色分类保存
- 支持多服务器资源下载
- 美观的图形界面
- 实时下载进度显示
- 支持断点续传
- 自动跳过已下载的卡面

## 系统要求

- Windows 10/11
- Python 3.8 或更高版本
- 网络连接

## 部署说明



## 目录结构

```
bestdori_app/
├── assets/          # 资源文件
│   ├── backgrounds/ # 背景图片
│   ├── icons/      # 图标
│   └── images/     # 其他图片
├── src/            # 源代码
│   ├── core/       # 核心功能
│   ├── gui/        # 图形界面
│   └── utils/      # 工具函数
└── requirements.txt # 依赖包列表
```

## 使用说明

1. 运行主程序：
   ```bash
   python src/gui/app.py
   ```

2. 在界面中选择：
   - 乐队（可选）
   - 角色（可选）
   - 乐器（可选）

3. 点击"开始下载"按钮
4. 选择保存目录
5. 等待下载完成

## 常见问题

1. 如果安装依赖包时出错：
   - 确保Python版本正确
   - 尝试使用国内镜像源：
     ```bash
     pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
     ```

2. 如果运行时提示缺少模块：
   - 重新运行 `pip install -r requirements.txt`
   - 检查Python环境变量是否正确设置

3. 如果下载速度较慢：
   - 检查网络连接
   - 尝试使用代理或VPN

## 注意事项

- 请确保网络连接稳定
- 下载过程中请勿关闭程序
- 建议使用稳定的网络环境
- 下载的卡面仅供个人使用

## 版本历史

- v1.0.0 (2024-03-31)
  - 初始版本发布
  - 实现基本下载功能
  - 支持多种筛选方式

## 许可证

MIT License

## 作者

alittlexu

## 致谢

感谢BanG Dream! 游戏开发团队 
