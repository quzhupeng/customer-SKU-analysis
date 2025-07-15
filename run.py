#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本
Application Startup Script
"""

import os
import sys

def check_dependencies():
    """检查依赖"""
    required_packages = ['flask', 'pandas', 'openpyxl', 'numpy']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"缺少依赖包: {', '.join(missing)}")
        print("请运行: pip install flask pandas openpyxl numpy")
        return False
    
    return True

def main():
    """主函数"""
    print("产品客户价值分析系统")
    print("=" * 40)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建必要目录
    dirs = ['uploads', 'exports', 'templates', 'static/css', 'static/js']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # 启动应用
    try:
        from app import app
        print("启动Flask应用...")
        print("访问地址: http://localhost:8080")
        print("按 Ctrl+C 停止服务")
        app.run(debug=True, host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
