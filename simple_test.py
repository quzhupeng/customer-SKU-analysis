#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本
Simple Test Script
"""

def test_basic_imports():
    """测试基本导入"""
    try:
        print("测试基本模块导入...")
        
        # 测试标准库
        import os
        import sys
        print("✓ 标准库导入成功")
        
        # 测试pandas
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        print("✓ pandas 工作正常")
        
        # 测试numpy
        import numpy as np
        arr = np.array([1, 2, 3])
        print("✓ numpy 工作正常")
        
        # 测试flask
        from flask import Flask
        app = Flask(__name__)
        print("✓ Flask 工作正常")
        
        # 测试openpyxl
        import openpyxl
        print("✓ openpyxl 工作正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 导入测试失败: {e}")
        return False

def test_custom_modules():
    """测试自定义模块"""
    try:
        print("\n测试自定义模块...")
        
        # 测试utils
        from utils import get_field_aliases, detect_field_type
        aliases = get_field_aliases()
        field_type = detect_field_type("物料名称")
        print(f"✓ utils模块: 检测到字段类型 '{field_type}'")
        
        # 测试analyzer（简单导入测试）
        from analyzer import DataAnalyzer
        print("✓ analyzer模块导入成功")
        
        # 测试exporter
        from exporter import ReportExporter
        print("✓ exporter模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 自定义模块测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    import os
    
    print("\n测试文件结构...")
    
    required_files = [
        'app.py', 'analyzer.py', 'utils.py', 'exporter.py',
        'templates/index.html', 'static/css/style.css', 'static/js/app.js'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主函数"""
    print("=" * 50)
    print("产品客户价值分析系统 - 简单测试")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_custom_modules,
        test_file_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试异常: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 基本测试通过！")
        print("\n尝试启动应用:")
        print("python app.py")
        print("或")
        print("python run.py")
    else:
        print("⚠️ 有测试失败，请检查环境配置")

if __name__ == '__main__':
    main()
