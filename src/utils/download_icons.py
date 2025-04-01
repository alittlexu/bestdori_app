import os
import requests
from PIL import Image
from io import BytesIO

# 图标配置
ICONS = {
    'bestdori': {
        'url': 'https://bestdori.com/assets/en/favicon.ico',
        'filename': 'bestdori.ico'
    },
    'download': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/download/v12/24px.svg',
        'filename': 'download.png'
    },
    'refresh': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/refresh/v12/24px.svg',
        'filename': 'refresh.png'
    },
    'search': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/search/v12/24px.svg',
        'filename': 'search.png'
    },
    'voice_download': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/music_note/v12/24px.svg',
        'filename': 'voice_download.png'
    },
    'play': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/play_arrow/v12/24px.svg',
        'filename': 'play.png'
    },
    'voice_search': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/audiotrack/v12/24px.svg',
        'filename': 'voice_search.png'
    },
    'import': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/upload/v12/24px.svg',
        'filename': 'import.png'
    },
    'export': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/download/v12/24px.svg',
        'filename': 'export.png'
    },
    'exit': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/exit_to_app/v12/24px.svg',
        'filename': 'exit.png'
    },
    'batch': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/playlist_add/v12/24px.svg',
        'filename': 'batch.png'
    },
    'history': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/history/v12/24px.svg',
        'filename': 'history.png'
    },
    'package': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/folder/v12/24px.svg',
        'filename': 'package.png'
    },
    'settings': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/settings/v12/24px.svg',
        'filename': 'settings.png'
    },
    'help': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/help/v12/24px.svg',
        'filename': 'help.png'
    },
    'about': {
        'url': 'https://fonts.gstatic.com/s/i/materialicons/info/v12/24px.svg',
        'filename': 'about.png'
    }
}

def convert_svg_to_png(svg_data, size=(24, 24)):
    """将SVG转换为PNG"""
    try:
        from cairosvg import svg2png
        png_data = svg2png(bytestring=svg_data, output_width=size[0], output_height=size[1])
        return png_data
    except ImportError:
        print("请安装cairosvg库以支持SVG转换: pip install cairosvg")
        return None

def download_icon(url, filename, icons_dir):
    """下载并保存图标"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 保存图标
        icon_path = os.path.join(icons_dir, filename)
        
        if url.endswith('.svg'):
            # 转换SVG为PNG
            png_data = convert_svg_to_png(response.content)
            if png_data:
                with open(icon_path, 'wb') as f:
                    f.write(png_data)
            else:
                # 如果转换失败，创建一个空白的PNG图标
                img = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
                img.save(icon_path, 'PNG')
        elif filename.endswith('.ico'):
            with open(icon_path, 'wb') as f:
                f.write(response.content)
        else:
            # 保存为PNG
            img = Image.open(BytesIO(response.content))
            img.save(icon_path, 'PNG')
            
        print(f"成功下载图标: {filename}")
        return True
    except Exception as e:
        print(f"下载图标失败 {filename}: {str(e)}")
        return False

def main():
    # 获取图标目录路径
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icons_dir = os.path.join(current_dir, 'assets', 'icons')
    
    # 确保图标目录存在
    os.makedirs(icons_dir, exist_ok=True)
    
    # 下载所有图标
    success_count = 0
    for icon_name, icon_info in ICONS.items():
        if download_icon(icon_info['url'], icon_info['filename'], icons_dir):
            success_count += 1
    
    print(f"\n下载完成! 成功: {success_count}/{len(ICONS)}")

if __name__ == '__main__':
    main() 