import sqlite3
import os
from typing import List, Dict, Tuple

class DatabaseManager:
    def __init__(self):
        """初始化数据库连接"""
        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        # 确保data目录存在
        data_dir = os.path.join(root_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        # 创建数据库连接
        db_path = os.path.join(data_dir, 'bestdori.db')
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        
        # 创建乐队表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bands (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        ''')
        
        # 创建角色表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            nickname TEXT NOT NULL,
            band_id INTEGER,
            FOREIGN KEY (band_id) REFERENCES bands (id)
        )
        ''')
        
        # 创建乐器表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS instruments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en TEXT NOT NULL,
            name_cn TEXT NOT NULL
        )
        ''')
        
        # 创建角色-乐器关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS character_instruments (
            character_id INTEGER,
            instrument_id INTEGER,
            PRIMARY KEY (character_id, instrument_id),
            FOREIGN KEY (character_id) REFERENCES characters (id),
            FOREIGN KEY (instrument_id) REFERENCES instruments (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_band(self, band_id, name):
        """添加乐队"""
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO bands (id, name) VALUES (?, ?)',
                      (band_id, name))
        self.conn.commit()
    
    def add_character(self, character_id, name, nickname, band_id, instruments):
        """添加角色及其乐器"""
        cursor = self.conn.cursor()
        
        # 添加角色
        cursor.execute('''
        INSERT OR REPLACE INTO characters (id, name, nickname, band_id)
        VALUES (?, ?, ?, ?)
        ''', (character_id, name, nickname, band_id))
        
        # 添加乐器
        for instrument in instruments:
            name_en, name_cn = instrument  # 解包英文和中文名称
            
            # 检查乐器是否已存在
            cursor.execute('''
            SELECT id FROM instruments 
            WHERE name_en = ? OR name_cn = ?
            ''', (name_en, name_cn))
            result = cursor.fetchone()
            
            if result:
                instrument_id = result[0]
            else:
                # 创建新乐器
                cursor.execute('''
                INSERT INTO instruments (name_en, name_cn)
                VALUES (?, ?)
                ''', (name_en, name_cn))
                instrument_id = cursor.lastrowid
            
            # 添加角色-乐器关联
            cursor.execute('''
            INSERT OR REPLACE INTO character_instruments (character_id, instrument_id)
            VALUES (?, ?)
            ''', (character_id, instrument_id))
        
        self.conn.commit()
    
    def get_all_bands(self):
        """获取所有乐队"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM bands ORDER BY id')
        return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    
    def get_all_instruments(self):
        """获取所有乐器"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name_en, name_cn FROM instruments ORDER BY name_cn')
        return [{'id': row[0], 'name_en': row[1], 'name_cn': row[2]} for row in cursor.fetchall()]
    
    def get_characters_by_band(self, band_id):
        """获取指定乐队的角色"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, name
        FROM characters
        WHERE band_id = ?
        ORDER BY id
        ''', (band_id,))
        return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    
    def get_characters_by_instrument(self, instrument_id):
        """获取指定乐器的角色"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT c.id, c.name, c.nickname, b.name as band_name, i.name_cn as instrument_name
        FROM characters c
        JOIN character_instruments ci ON c.id = ci.character_id
        JOIN bands b ON c.band_id = b.id
        JOIN instruments i ON ci.instrument_id = i.id
        WHERE ci.instrument_id = ?
        ORDER BY c.id
        ''', (instrument_id,))
        return [{'id': row[0], 'name': row[1], 'nickname': row[2], 'band_name': row[3], 'instrument_name': row[4]} 
                for row in cursor.fetchall()]
    
    def get_characters_by_star(self, star):
        """获取指定星级的角色"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT c.id, c.name, c.nickname, b.name as band_name
        FROM characters c
        JOIN bands b ON c.band_id = b.id
        WHERE c.id BETWEEN ? AND ?
        ORDER BY c.id
        ''', (star * 1000, (star + 1) * 1000 - 1))
        return [{'id': row[0], 'name': row[1], 'nickname': row[2], 'band_name': row[3]} 
                for row in cursor.fetchall()]
    
    def get_characters_by_band_and_instrument(self, band_id, instrument_id):
        """获取特定乐队和乐器对应的角色"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT c.id, c.name
        FROM characters c
        JOIN character_instruments ci ON c.id = ci.character_id
        WHERE c.band_id = ? AND ci.instrument_id = ?
        ORDER BY c.id
        ''', (band_id, instrument_id))
        return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close() 