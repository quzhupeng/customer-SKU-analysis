#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字段检测功能
"""

import pandas as pd
from utils import detect_field_type, get_field_aliases
from analyzer import DataAnalyzer

def test_field_detection():
    """测试字段检测功能"""
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'SKU': ['产品A', '产品B', '产品C'],
        '客户名称': ['客户1', '客户2', '客户3'],
        '地区': ['北京', '上海', '广州'],
        '数量': [100, 200, 150],
        '毛利': [1000, 2000, 1500],
        '金额': [5000, 10000, 7500],
        '未知列': ['值1', '值2', '值3']
    })
    
    # 保存为Excel文件
    test_file = 'test_detection.xlsx'
    test_data.to_excel(test_file, index=False)
    
    print("=== 字段别名配置 ===")
    aliases = get_field_aliases()
    for field_type, alias_list in aliases.items():
        print(f"{field_type}: {alias_list}")
    
    print("\n=== 单独测试字段检测 ===")
    for column in test_data.columns:
        field_type = detect_field_type(column)
        print(f"'{column}' -> {field_type}")
    
    print("\n=== 使用分析器测试 ===")
    try:
        analyzer = DataAnalyzer(test_file, 'Sheet1')
        result = analyzer.detect_fields()
        
        print("检测到的字段:")
        for field_type, column in result['detected_fields'].items():
            print(f"  {field_type}: {column}")
        
        print("\n列信息:")
        for column, info in result['column_info'].items():
            print(f"  {column}: {info['field_type']} (样本: {info['sample_values']})")
            
    except Exception as e:
        print(f"分析器测试失败: {e}")
    
    # 清理测试文件
    import os
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == '__main__':
    test_field_detection()
