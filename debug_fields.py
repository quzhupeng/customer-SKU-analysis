#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试字段识别问题
Debug Field Recognition Issue
"""

import pandas as pd
from utils import detect_field_type, clean_column_name, get_field_aliases

def debug_field_detection():
    """调试字段检测"""
    print("=" * 60)
    print("调试字段识别问题")
    print("=" * 60)
    
    # 1. 检查示例数据的列名
    print("1. 检查示例数据的实际列名:")
    try:
        df = pd.read_excel('示例数据.xlsx', sheet_name='分单品')
        print(f"   数据形状: {df.shape}")
        print("   列名列表:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. '{col}' (类型: {type(col).__name__})")
    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")
        return
    
    # 2. 检查字段别名配置
    print("\n2. 检查字段别名配置:")
    aliases = get_field_aliases()
    for field_type, alias_list in aliases.items():
        print(f"   {field_type}: {alias_list}")
    
    # 3. 测试字段识别
    print("\n3. 测试每个列的字段识别:")
    for col in df.columns:
        cleaned = clean_column_name(col)
        field_type = detect_field_type(col)
        print(f"   '{col}' -> 清理后: '{cleaned}' -> 字段类型: {field_type}")
    
    # 4. 手动测试关键字段
    print("\n4. 手动测试关键字段识别:")
    test_columns = ['物料名称', '客户名称', '地区', '数量', '毛利', '金额']
    for test_col in test_columns:
        field_type = detect_field_type(test_col)
        print(f"   '{test_col}' -> {field_type}")
    
    # 5. 测试analyzer的字段检测
    print("\n5. 测试analyzer的字段检测:")
    try:
        from analyzer import DataAnalyzer
        analyzer = DataAnalyzer('示例数据.xlsx', '分单品')
        fields = analyzer.detect_fields()
        
        print("   检测结果:")
        detected = fields['detected_fields']
        for field_type, column in detected.items():
            print(f"   {field_type}: {column}")
        
        print("\n   缺失的字段:")
        expected_fields = ['product', 'customer', 'region', 'quantity', 'profit', 'amount']
        for field in expected_fields:
            if field not in detected:
                print(f"   ❌ {field}")
            else:
                print(f"   ✅ {field}: {detected[field]}")
                
    except Exception as e:
        print(f"   ❌ analyzer测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_specific_column():
    """测试特定列名"""
    print("\n" + "=" * 60)
    print("测试特定列名识别")
    print("=" * 60)
    
    # 测试可能的问题列名
    test_cases = [
        '物料名称',
        ' 物料名称 ',
        '物料名称\n',
        '物料名称\t',
        'SKU',
        '产品名称',
        '存货名称'
    ]
    
    for test_col in test_cases:
        print(f"测试: '{repr(test_col)}'")
        cleaned = clean_column_name(test_col)
        field_type = detect_field_type(test_col)
        print(f"  清理后: '{cleaned}'")
        print(f"  字段类型: {field_type}")
        print()

def main():
    debug_field_detection()
    test_specific_column()

if __name__ == '__main__':
    main()
