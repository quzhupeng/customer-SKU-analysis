#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用测试脚本
Application Test Script
"""

import sys
import os

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        import pandas as pd
        print("✓ pandas 导入成功")
    except ImportError as e:
        print(f"✗ pandas 导入失败: {e}")
        return False
    
    try:
        import openpyxl
        print("✓ openpyxl 导入成功")
    except ImportError as e:
        print(f"✗ openpyxl 导入失败: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy 导入成功")
    except ImportError as e:
        print(f"✗ numpy 导入失败: {e}")
        return False
    
    try:
        from flask import Flask
        print("✓ Flask 导入成功")
    except ImportError as e:
        print(f"✗ Flask 导入失败: {e}")
        return False
    
    return True

def test_custom_modules():
    """测试自定义模块"""
    print("\n测试自定义模块...")
    
    try:
        from utils import get_field_aliases, detect_field_type
        print("✓ utils 模块导入成功")
        
        # 测试函数
        aliases = get_field_aliases()
        print(f"✓ 字段别名配置: {len(aliases)} 个字段类型")
        
        field_type = detect_field_type("物料名称")
        print(f"✓ 字段检测功能: '物料名称' -> {field_type}")
        
    except Exception as e:
        print(f"✗ utils 模块测试失败: {e}")
        return False
    
    try:
        from analyzer import DataAnalyzer
        print("✓ analyzer 模块导入成功")
    except Exception as e:
        print(f"✗ analyzer 模块导入失败: {e}")
        return False
    
    try:
        from exporter import ReportExporter
        print("✓ exporter 模块导入成功")
    except Exception as e:
        print(f"✗ exporter 模块导入失败: {e}")
        return False
    
    return True

def test_flask_app():
    """测试Flask应用"""
    print("\n测试Flask应用...")
    
    try:
        from app import app
        print("✓ Flask应用导入成功")
        
        # 测试应用配置
        print(f"✓ 应用配置: {app.config['MAX_CONTENT_LENGTH']} bytes 最大文件大小")
        
        # 测试路由
        with app.test_client() as client:
            response = client.get('/')
            print(f"✓ 主页路由测试: 状态码 {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask应用测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n测试文件结构...")
    
    required_files = [
        'app.py',
        'analyzer.py', 
        'utils.py',
        'exporter.py',
        'requirements.txt',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    required_dirs = [
        'uploads',
        'exports',
        'templates',
        'static',
        'static/css',
        'static/js'
    ]
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 缺失")
            all_good = False
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ 缺失")
            all_good = False
    
    return all_good

def main():
    """主测试函数"""
    print("=" * 50)
    print("产品客户价值分析系统 - 应用测试")
    print("=" * 50)
    
    tests = [
        ("文件结构", test_file_structure),
        ("模块导入", test_imports),
        ("自定义模块", test_custom_modules),
        ("Flask应用", test_flask_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "="*50)
    print("测试结果总结:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！应用可以正常运行。")
        print("\n启动应用命令: python app.py")
        print("访问地址: http://localhost:5000")
    else:
        print(f"\n⚠️  有 {len(results) - passed} 项测试失败，请检查相关问题。")
    
    return passed == len(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
