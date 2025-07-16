#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from utils import detect_field_type, get_field_aliases

def debug_latest_file():
    """调试最新上传的文件"""
    uploads_dir = 'uploads'
    
    # 获取最新的文件
    files = []
    for filename in os.listdir(uploads_dir):
        if filename.endswith('.xlsx'):
            filepath = os.path.join(uploads_dir, filename)
            files.append((filepath, os.path.getmtime(filepath)))
    
    if not files:
        print("没有找到Excel文件")
        return
    
    # 按修改时间排序，获取最新的文件
    latest_file = sorted(files, key=lambda x: x[1], reverse=True)[0][0]
    print(f"最新文件: {latest_file}")
    
    # 读取文件
    try:
        df = pd.read_excel(latest_file)
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        
        # 检测每个字段类型
        print("\n字段检测结果:")
        detected_fields = {}
        for column in df.columns:
            field_type = detect_field_type(column)
            print(f"  {column} -> {field_type}")
            if field_type != 'unknown':
                detected_fields[field_type] = column
        
        print(f"\n检测到的字段映射: {detected_fields}")
        
        # 显示前几行数据
        print(f"\n前5行数据:")
        print(df.head())
        
        # 检查字段别名
        print(f"\n字段别名配置:")
        aliases = get_field_aliases()
        for field_type, alias_list in aliases.items():
            print(f"  {field_type}: {alias_list[:5]}...")  # 只显示前5个
            
    except Exception as e:
        print(f"读取文件失败: {e}")

if __name__ == "__main__":
    debug_latest_file()
