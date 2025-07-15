#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的功能
Test Fixed Functionality
"""

import pandas as pd
import os

def test_analyzer():
    """测试分析器功能"""
    print("测试分析器功能...")
    
    try:
        from analyzer import DataAnalyzer
        from utils import detect_field_type, clean_column_name
        
        # 测试字段检测
        print("✓ 模块导入成功")
        
        # 测试列名清理
        test_names = ['物料名称', '  客户名称  ', None, 123, '数量\n']
        for name in test_names:
            cleaned = clean_column_name(name)
            print(f"  '{name}' -> '{cleaned}'")
        
        # 测试字段类型检测
        test_columns = ['物料名称', '客户名称', '数量', '毛利', '未知列']
        for col in test_columns:
            field_type = detect_field_type(col)
            print(f"  '{col}' -> {field_type}")
        
        # 测试示例数据
        if os.path.exists('示例数据.xlsx'):
            print("\n测试示例数据...")
            analyzer = DataAnalyzer('示例数据.xlsx', '分单品')
            fields = analyzer.detect_fields()
            print(f"✓ 检测到字段: {list(fields['detected_fields'].keys())}")
            print(f"✓ 数据行数: {fields['total_rows']}")
        else:
            print("⚠️ 示例数据文件不存在")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("测试修复后的功能")
    print("=" * 50)
    
    success = test_analyzer()
    
    if success:
        print("\n🎉 测试通过！现在可以正常使用应用了。")
        print("\n启动应用:")
        print("python3 -c \"from app import app; app.run(host='127.0.0.1', port=8080, debug=True)\"")
        print("\n访问: http://localhost:8080")
    else:
        print("\n❌ 测试失败，需要进一步调试")

if __name__ == '__main__':
    main()
