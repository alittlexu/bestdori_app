"""
路径工具函数 - 用于构建统一的下载路径结构
"""
import os
from .config_manager import get_config_manager


def get_download_path(download_type='card'):
    """
    获取下载路径，结构：<用户设置的根路径>/Bestdori/<类型>/
    
    参数:
        download_type: 下载类型，可选值：
            - 'card': 卡面下载
            - 'animation': 动态卡面下载
            - 'voice': 语音下载
    
    返回:
        完整的下载路径
    """
    config_manager = get_config_manager()
    root_path = config_manager.get_download_root_path()
    
    # 如果根路径未设置，返回None（需要用户先设置）
    if not root_path:
        return None
    
    # 构建路径：<root_path>/Bestdori/<type>/
    download_path = os.path.join(root_path, 'Bestdori', download_type)
    
    # 确保目录存在
    try:
        os.makedirs(download_path, exist_ok=True)
    except Exception as e:
        raise Exception(f"创建下载目录失败: {e}")
    
    return download_path


def ensure_download_path(download_type='card'):
    """
    确保下载路径存在，如果根路径未设置则抛出异常
    
    参数:
        download_type: 下载类型
    
    返回:
        完整的下载路径
    
    抛出:
        ValueError: 如果根路径未设置
        OSError: 如果创建目录失败
    """
    config_manager = get_config_manager()
    root_path = config_manager.get_download_root_path()
    
    if not root_path:
        raise ValueError("请先设置下载根路径")
    
    # 构建路径：<root_path>/Bestdori/<type>/
    download_path = os.path.join(root_path, 'Bestdori', download_type)
    
    # 确保目录存在
    os.makedirs(download_path, exist_ok=True)
    
    return download_path
