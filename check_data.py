#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据文件
Check Data File
"""

import pandas as pd
import numpy as np

def check_existing_data():
    """检查现有数据文件"""
    print("检查现有示例数据文件...")
    
    try:
        # 读取Excel文件
        excel_file = pd.ExcelFile('示例数据.xlsx')
        print(f"工作表: {excel_file.sheet_names}")
        
        # 检查分单品sheet
        df = pd.read_excel('示例数据.xlsx', sheet_name='分单品')
        print(f"\n分单品数据形状: {df.shape}")
        print("列名:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. '{col}'")
        
        # 测试字段识别
        print("\n测试字段识别:")
        from utils import detect_field_type
        
        for col in df.columns:
            field_type = detect_field_type(col)
            print(f"  '{col}' -> {field_type}")
        
        return True
        
    except Exception as e:
        print(f"检查失败: {e}")
        return False

def create_simple_test_data():
    """创建简单的测试数据"""
    print("\n创建简单测试数据...")
    
    # 创建测试数据
    data = {
        '物料名称': ['钢材A', '钢材B', '铝材A', '铜材A', '塑料A'],
        '客户名称': ['客户1', '客户2', '客户3', '客户4', '客户5'],
        '地区': ['华东', '华南', '华北', '华中', '西南'],
        '数量': [100, 200, 150, 300, 250],
        '毛利': [1000, 2000, 1500, 3000, 2500],
        '金额': [5000, 10000, 7500, 15000, 12500],
        '单价': [50, 50, 50, 50, 50]
    }
    
    df = pd.DataFrame(data)
    
    # 保存为Excel
    with pd.ExcelWriter('测试数据.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='分单品', index=False)
        df.to_excel(writer, sheet_name='分客户', index=False)
        df.to_excel(writer, sheet_name='分地区', index=False)
    
    print("✅ 测试数据已创建: 测试数据.xlsx")
    
    # 测试字段识别
    print("\n测试新数据的字段识别:")
    from utils import detect_field_type
    
    for col in df.columns:
        field_type = detect_field_type(col)
        print(f"  '{col}' -> {field_type}")
    
    # 测试analyzer
    print("\n测试analyzer:")
    try:
        from analyzer import DataAnalyzer
        analyzer = DataAnalyzer('测试数据.xlsx', '分单品')
        fields = analyzer.detect_fields()
        
        print("检测结果:")
        for field_type, column in fields['detected_fields'].items():
            print(f"  {field_type}: {column}")
            
    except Exception as e:
        print(f"analyzer测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("=" * 50)
    print("数据文件检查和调试")
    print("=" * 50)
    
    # 检查现有数据
    if not check_existing_data():
        print("现有数据检查失败，创建新的测试数据")
    
    # 创建简单测试数据
    create_simple_test_data()

if __name__ == '__main__':
    main()
