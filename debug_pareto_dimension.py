#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帕累托维度切换问题调试脚本
Debug script for Pareto dimension switching issues
"""

import pandas as pd
import json
from analyzer import DataAnalyzer
from utils import get_field_aliases, detect_field_type

def debug_pareto_dimension_issue():
    """调试帕累托维度切换问题"""
    print("=" * 80)
    print("帕累托维度切换问题调试")
    print("=" * 80)

    # 测试文件路径
    test_files = [
        "实际上传excel/出口部单品利润明细汇总1-5月.xlsx"
    ]

    print(f"开始测试，文件数量: {len(test_files)}")
    
    for file_path in test_files:
        try:
            print(f"\n📁 测试文件: {file_path}")
            
            # 读取Excel文件的所有sheet
            excel_file = pd.ExcelFile(file_path)
            print(f"   工作表: {excel_file.sheet_names}")
            
            # 测试第一个工作表
            sheet_name = excel_file.sheet_names[0]
            print(f"   使用工作表: {sheet_name}")
            
            # 创建分析器
            analyzer = DataAnalyzer(file_path, sheet_name)
            
            # 检测字段
            field_detection = analyzer.detect_fields()
            print(f"   检测到的字段: {field_detection['detected_fields']}")
            
            # 测试不同维度的帕累托分析
            dimensions_to_test = ['profit', 'quantity', 'amount']
            
            for dimension in dimensions_to_test:
                print(f"\n   🔍 测试维度: {dimension}")
                
                try:
                    # 验证字段
                    field_validation = analyzer.validate_fields('product')
                    if not field_validation['is_valid']:
                        print(f"      ❌ 字段验证失败: {field_validation['missing_fields']}")
                        continue
                    
                    # 执行分析
                    unit_confirmations = {
                        'quantity': 'kg',
                        'amount': 'yuan'
                    }
                    
                    result = analyzer.analyze('product', unit_confirmations, dimension)
                    pareto_data = result['additional_analysis']['pareto_analysis']
                    
                    print(f"      ✅ 分析成功")
                    print(f"      - 维度: {pareto_data.get('dimension', 'unknown')}")
                    print(f"      - 维度信息: {pareto_data.get('dimension_info', {})}")
                    print(f"      - 数据行数: {len(pareto_data.get('pareto_data', []))}")
                    print(f"      - 核心项目数: {pareto_data.get('core_items_count', 0)}")
                    
                    # 检查数据结构
                    if pareto_data.get('pareto_data'):
                        first_item = pareto_data['pareto_data'][0]
                        print(f"      - 数据列名: {list(first_item.keys())}")
                        
                        # 检查字段映射
                        field_mapping = analyzer.field_mapping
                        if dimension in field_mapping:
                            actual_field = field_mapping[dimension]
                            print(f"      - 实际字段名: {actual_field}")
                            if actual_field in first_item:
                                print(f"      - 字段值示例: {first_item[actual_field]}")
                            else:
                                print(f"      ❌ 字段 '{actual_field}' 不在数据中")
                        else:
                            print(f"      ❌ 维度 '{dimension}' 不在字段映射中")
                    
                except Exception as e:
                    print(f"      ❌ 分析失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
        except Exception as e:
            print(f"   ❌ 文件处理失败: {str(e)}")
            continue
    
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)

if __name__ == "__main__":
    debug_pareto_dimension_issue()
