#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分析修复功能
"""

import pandas as pd
import numpy as np
from analyzer import DataAnalyzer
from utils import validate_required_fields, safe_to_dict

def create_test_data():
    """创建测试数据"""
    # 产品分析测试数据
    product_data = pd.DataFrame({
        'SKU': ['产品A', '产品B', '产品C', '产品D'],
        '数量': [100, 200, 150, 300],
        '毛利': [1000, 2000, 1500, np.nan],  # 包含NaN值
        '金额': [5000, 10000, 7500, 15000],
        '成本': [4000, 8000, 6000, 12000]
    })
    
    # 客户分析测试数据
    customer_data = pd.DataFrame({
        '客户名称': ['客户A', '客户B', '客户C'],
        '金额': [50000, 30000, 20000],
        '毛利': [5000, 3000, np.inf],  # 包含inf值
        '数量': [500, 300, 200]
    })
    
    return product_data, customer_data

def test_required_fields():
    """测试必需字段验证"""
    print("=== 测试必需字段验证 ===")
    
    # 测试产品分析
    product_fields = {'product': 'SKU', 'quantity': '数量', 'profit': '毛利'}
    missing = validate_required_fields(product_fields, 'product')
    print(f"产品分析缺失字段: {missing}")
    
    # 测试客户分析
    customer_fields = {'customer': '客户名称', 'amount': '金额', 'profit': '毛利'}
    missing = validate_required_fields(customer_fields, 'customer')
    print(f"客户分析缺失字段: {missing}")
    
    # 测试缺失字段的情况
    incomplete_fields = {'product': 'SKU'}  # 缺少quantity和profit
    missing = validate_required_fields(incomplete_fields, 'product')
    print(f"不完整字段缺失: {missing}")

def test_safe_to_dict():
    """测试安全的字典转换"""
    print("\n=== 测试安全字典转换 ===")
    
    # 创建包含NaN和inf的测试数据
    test_df = pd.DataFrame({
        '正常值': [1, 2, 3],
        'NaN值': [1, np.nan, 3],
        'inf值': [1, np.inf, -np.inf],
        '字符串': ['a', 'b', 'c']
    })
    
    print("原始数据:")
    print(test_df)
    
    # 使用安全转换
    safe_result = safe_to_dict(test_df)
    print("\n安全转换结果:")
    for i, record in enumerate(safe_result):
        print(f"记录{i}: {record}")

def test_analysis():
    """测试完整分析流程"""
    print("\n=== 测试完整分析流程 ===")
    
    product_data, customer_data = create_test_data()
    
    # 测试产品分析
    print("\n--- 产品分析测试 ---")
    product_data.to_excel('test_product.xlsx', index=False)
    
    try:
        analyzer = DataAnalyzer('test_product.xlsx', 'Sheet1')
        
        # 检测字段
        field_result = analyzer.detect_fields()
        print("检测到的字段:", field_result['detected_fields'])
        
        # 验证字段
        validation = analyzer.validate_fields('product')
        print("字段验证结果:", validation)
        
        if validation['is_valid']:
            # 执行分析
            result = analyzer.analyze('product', {})
            print("产品分析成功完成")
            print(f"聚合数据行数: {len(result['aggregated_data'])}")
        else:
            print(f"字段验证失败: {validation['missing_fields']}")
            
    except Exception as e:
        print(f"产品分析失败: {e}")
    
    # 测试客户分析
    print("\n--- 客户分析测试 ---")
    customer_data.to_excel('test_customer.xlsx', index=False)
    
    try:
        analyzer = DataAnalyzer('test_customer.xlsx', 'Sheet1')
        
        # 检测字段
        field_result = analyzer.detect_fields()
        print("检测到的字段:", field_result['detected_fields'])
        
        # 验证字段
        validation = analyzer.validate_fields('customer')
        print("字段验证结果:", validation)
        
        if validation['is_valid']:
            # 执行分析
            result = analyzer.analyze('customer', {})
            print("客户分析成功完成")
            print(f"聚合数据行数: {len(result['aggregated_data'])}")
        else:
            print(f"字段验证失败: {validation['missing_fields']}")
            
    except Exception as e:
        print(f"客户分析失败: {e}")
    
    # 清理测试文件
    import os
    for file in ['test_product.xlsx', 'test_customer.xlsx']:
        if os.path.exists(file):
            os.remove(file)

if __name__ == '__main__':
    test_required_fields()
    test_safe_to_dict()
    test_analysis()
