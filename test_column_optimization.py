#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试列设置功能优化
Test Column Settings Optimization

Author: Kiro AI Assistant
Date: 2025-07-19
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyzer import DataAnalyzer

def test_column_optimization():
    """测试列设置功能优化"""
    print("=== 测试列设置功能优化 ===")
    
    # 查找测试文件
    test_files = []
    upload_dir = 'uploads'
    if os.path.exists(upload_dir):
        for file in os.listdir(upload_dir):
            if file.endswith('.xlsx'):
                test_files.append(os.path.join(upload_dir, file))
    
    if not test_files:
        print("未找到测试文件，请先上传Excel文件")
        return
    
    # 使用最新的文件
    test_file = max(test_files, key=os.path.getctime)
    print(f"使用测试文件: {test_file}")
    
    try:
        # 读取Excel文件获取sheet列表
        excel_file = pd.ExcelFile(test_file)
        sheet_name = excel_file.sheet_names[0]
        print(f"使用工作表: {sheet_name}")
        
        # 创建分析器
        analyzer = DataAnalyzer(test_file, sheet_name)
        
        # 检测字段
        field_detection = analyzer.detect_fields()
        print(f"\n字段检测结果:")
        for field_type, column in field_detection['detected_fields'].items():
            print(f"  {field_type}: {column}")
        
        # 执行分析
        unit_confirmations = {
            'quantity': 'kg',
            'amount': 'yuan'
        }
        
        print(f"\n执行客户分析...")
        result = analyzer.analyze('customer', unit_confirmations, 'profit')
        
        # 检查聚合数据的列
        aggregated_data = result['aggregated_data']
        if aggregated_data:
            print(f"\n聚合数据列数: {len(aggregated_data)}")
            if len(aggregated_data) > 0:
                columns = list(aggregated_data[0].keys())
                print(f"可用列: {columns}")
                
                # 检查新增的标准化列
                expected_columns = [
                    '采购金额(万元)', '毛利贡献(万元)', '采购数量(吨)', '客户毛利率'
                ]
                
                found_columns = []
                missing_columns = []
                
                for col in expected_columns:
                    if col in columns:
                        found_columns.append(col)
                    else:
                        missing_columns.append(col)
                
                print(f"\n标准化列检查:")
                print(f"  找到的列: {found_columns}")
                if missing_columns:
                    print(f"  缺失的列: {missing_columns}")
                else:
                    print(f"  ✓ 所有标准化列都已添加")
                
                # 显示前几行数据示例
                print(f"\n数据示例 (前3行):")
                for i, row in enumerate(aggregated_data[:3]):
                    print(f"  行 {i+1}:")
                    for col in found_columns:
                        if col in row:
                            value = row[col]
                            if isinstance(value, (int, float)):
                                print(f"    {col}: {value:.2f}")
                            else:
                                print(f"    {col}: {value}")
        
        print(f"\n✓ 列设置功能优化测试完成")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_frontend_integration():
    """测试前端集成"""
    print("\n=== 测试前端集成 ===")
    
    # 检查关键文件是否存在
    files_to_check = [
        'templates/index.html',
        'static/js/app.js',
        'static/css/style.css'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
    
    # 检查HTML中是否包含列设置按钮
    html_file = 'templates/index.html'
    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'columnSettingsBtn' in content:
            print("✓ HTML包含列设置按钮")
        else:
            print("✗ HTML缺少列设置按钮")
            
        if 'column-controls' in content:
            print("✓ HTML包含列控制区域")
        else:
            print("✗ HTML缺少列控制区域")
    
    # 检查CSS中是否包含相关样式
    css_file = 'static/css/style.css'
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_styles = [
            'column-settings-menu',
            'data-bar-cell',
            'quadrant-badge'
        ]
        
        for style in required_styles:
            if style in content:
                print(f"✓ CSS包含 {style} 样式")
            else:
                print(f"✗ CSS缺少 {style} 样式")
    
    # 检查JavaScript中是否包含相关函数
    js_file = 'static/js/app.js'
    if os.path.exists(js_file):
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_functions = [
            'initializeColumnSettings',
            'getVisibleColumns',
            'addDataBar'
        ]
        
        for func in required_functions:
            if func in content:
                print(f"✓ JavaScript包含 {func} 函数")
            else:
                print(f"✗ JavaScript缺少 {func} 函数")

if __name__ == '__main__':
    test_column_optimization()
    test_frontend_integration()
    print(f"\n=== 测试完成 ===")