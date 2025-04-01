import json
import os
from src.utils.database import DatabaseManager

def init_database():
    """初始化数据库数据"""
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # 确保data目录存在
    data_dir = os.path.join(root_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 删除旧的数据库文件
    db_path = os.path.join(data_dir, 'bestdori.db')
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print("已删除旧的数据库文件")
    except Exception as e:
        print(f"删除旧数据库文件失败: {e}")
    
    # 创建新的数据库连接
    db = DatabaseManager()
    
    # 读取角色列表
    json_path = os.path.join(root_dir, 'character_list.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 添加乐队和成员
    for group in data['groups']:
        # 将乐队ID从1开始编号
        new_band_id = group['id'] + 1 if group['id'] == 0 else group['id']
        print(f"添加乐队: {group['name']} (原始ID: {group['id']}, 新ID: {new_band_id})")
        db.add_band(new_band_id, group['name'])
        
        # 添加成员
        for member in group['members']:
            # 只使用英文和中文的乐器名称
            instruments = [(member['instruments'][0], member['instruments'][2])]  # 英文和中文
            print(f"添加成员: {member['name']} (ID: {member['id']}, 乐队ID: {new_band_id})")
            db.add_character(
                member['id'],
                member['name'],
                member['nickname'],
                new_band_id,  # 使用新的乐队ID
                instruments
            )
    
    # 验证数据
    cursor = db.conn.cursor()
    cursor.execute('SELECT id, name FROM bands ORDER BY id')
    bands = cursor.fetchall()
    print("\n已添加的乐队:")
    for band in bands:
        print(f"ID: {band[0]}, 名称: {band[1]}")
        cursor.execute('SELECT id, name FROM characters WHERE band_id = ?', (band[0],))
        members = cursor.fetchall()
        print("成员:")
        for member in members:
            print(f"  - ID: {member[0]}, 名称: {member[1]}")
    
    print("\n数据库初始化完成！")

if __name__ == "__main__":
    init_database() 