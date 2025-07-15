#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单启动脚本
Simple Start Script
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 50)
    print("产品客户价值分析系统")
    print("=" * 50)
    
    # 检查基本依赖
    try:
        import flask
        import pandas
        import openpyxl
        import numpy
        print("✓ 依赖包检查通过")
    except ImportError as e:
        print(f"✗ 缺少依赖包: {e}")
        print("请运行: pip install flask pandas openpyxl numpy")
        return
    
    # 创建必要目录
    dirs = ['uploads', 'exports']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # 导入并启动应用
    try:
        from app import app
        
        print("正在启动Flask应用...")
        print("访问地址: http://localhost:8080")
        print("按 Ctrl+C 停止服务")
        print("=" * 50)
        
        # 启动应用
        app.run(
            debug=True,
            host='0.0.0.0',
            port=8080,
            use_reloader=False  # 避免重载问题
        )
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
