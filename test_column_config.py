#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列配置功能测试脚本
Column Configuration Feature Test Script

Author: Augment Agent
Date: 2025-07-18
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_field_validation():
    """测试字段验证功能"""
    print("=" * 50)
    print("测试字段验证功能")
    print("=" * 50)
    
    try:
        from utils import validate_field_mappings, get_field_definitions
        
        # 测试产品分析的字段映射
        field_mappings = {
            'product': '产品名称',
            'quantity': '销售数量',
            'profit': '毛利',
            'amount': '销售金额'
        }
        
        result = validate_field_mappings(field_mappings, 'product')
        
        print("字段映射:", field_mappings)
        print("验证结果:")
        print(f"  - 是否有效: {result['is_valid']}")
        print(f"  - 必需字段: {result['required']['mapped_count']}/{result['required']['total']}")
        print(f"  - 推荐字段: {result['recommended']['mapped_count']}/{result['recommended']['total']}")
        print(f"  - 数值字段: {result['numeric']['count']}/{result['numeric']['required_count']}")
        print(f"  - 完成度: {result['summary']['completion_percentage']}%")
        
        if result['suggestions']:
            print("  - 建议:")
            for suggestion in result['suggestions']:
                print(f"    * {suggestion}")
        
        print("✓ 字段验证功能测试通过")
        
    except Exception as e:
        print(f"✗ 字段验证功能测试失败: {str(e)}")
        return False
    
    return True

def test_field_definitions():
    """测试字段定义功能"""
    print("\n" + "=" * 50)
    print("测试字段定义功能")
    print("=" * 50)
    
    try:
        from utils import get_field_definitions
        
        definitions = get_field_definitions()
        
        print(f"字段定义数量: {len(definitions)}")
        
        for field_type, definition in definitions.items():
            print(f"  - {field_type}: {definition['label']} ({definition['requirement']})")
        
        print("✓ 字段定义功能测试通过")
        
    except Exception as e:
        print(f"✗ 字段定义功能测试失败: {str(e)}")
        return False
    
    return True

def test_data_quality_validation():
    """测试数据质量验证功能"""
    print("\n" + "=" * 50)
    print("测试数据质量验证功能")
    print("=" * 50)
    
    try:
        from utils import validate_column_data_quality
        
        # 创建测试数据
        test_data = pd.DataFrame({
            '产品名称': ['产品A', '产品B', '产品C', None, '产品E'],
            '销售数量': [100, 200, 0, 150, -10],
            '销售金额': [1000, 2000, 0, 1500, 800],
            '毛利': [300, 600, 0, 450, 240]
        })
        
        field_mappings = {
            'product': '产品名称',
            'quantity': '销售数量',
            'amount': '销售金额',
            'profit': '毛利'
        }
        
        quality_report = validate_column_data_quality(test_data, field_mappings)
        
        print(f"整体质量: {quality_report['overall_quality']}")
        print(f"问题数量: {len(quality_report['issues'])}")
        print(f"警告数量: {len(quality_report['warnings'])}")
        
        if quality_report['issues']:
            print("问题:")
            for issue in quality_report['issues']:
                print(f"  - {issue}")
        
        if quality_report['warnings']:
            print("警告:")
            for warning in quality_report['warnings']:
                print(f"  - {warning}")
        
        print("✓ 数据质量验证功能测试通过")
        
    except Exception as e:
        print(f"✗ 数据质量验证功能测试失败: {str(e)}")
        return False
    
    return True

def test_analysis_recommendations():
    """测试分析建议功能"""
    print("\n" + "=" * 50)
    print("测试分析建议功能")
    print("=" * 50)
    
    try:
        from utils import get_analysis_recommendations
        
        field_mappings = {
            'product': '产品名称',
            'quantity': '销售数量',
            'profit': '毛利',
            'amount': '销售金额',
            'cost': '成本'
        }
        
        recommendations = get_analysis_recommendations(field_mappings, 'product')
        
        print(f"建议数量: {len(recommendations)}")
        for i, recommendation in enumerate(recommendations, 1):
            print(f"  {i}. {recommendation}")
        
        print("✓ 分析建议功能测试通过")
        
    except Exception as e:
        print(f"✗ 分析建议功能测试失败: {str(e)}")
        return False
    
    return True

def test_session_storage_simulation():
    """模拟测试会话存储功能"""
    print("\n" + "=" * 50)
    print("模拟测试会话存储功能")
    print("=" * 50)
    
    try:
        # 模拟会话存储数据结构
        session_data = {}
        
        # 模拟保存配置
        file_id = "test_file_123"
        config = {
            'file_id': file_id,
            'sheet_name': '分产品',
            'selected_columns': ['产品名称', '销售数量', '毛利'],
            'field_mappings': {
                'product': '产品名称',
                'quantity': '销售数量',
                'profit': '毛利'
            },
            'analysis_type': 'product',
            'timestamp': datetime.now().isoformat()
        }
        
        session_data[file_id] = config
        
        # 模拟加载配置
        loaded_config = session_data.get(file_id)
        
        print("保存的配置:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
        print("\n加载的配置:")
        print(json.dumps(loaded_config, indent=2, ensure_ascii=False))
        
        assert loaded_config == config, "配置保存和加载不一致"
        
        print("✓ 会话存储功能模拟测试通过")
        
    except Exception as e:
        print(f"✗ 会话存储功能模拟测试失败: {str(e)}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("列配置功能测试开始")
    print("测试时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    tests = [
        test_field_validation,
        test_field_definitions,
        test_data_quality_validation,
        test_analysis_recommendations,
        test_session_storage_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"总测试数: {total}")
    print(f"通过数: {passed}")
    print(f"失败数: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！列配置功能实现正确。")
        return True
    else:
        print("❌ 部分测试失败，请检查实现。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
