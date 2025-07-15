#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找可用端口并启动应用
Find Available Port and Start App
"""

import socket
import sys
import os

def find_free_port(start_port=8080, max_port=9000):
    """查找可用端口"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def main():
    print("=" * 50)
    print("产品客户价值分析系统 - 端口检测启动")
    print("=" * 50)
    
    # 查找可用端口
    port = find_free_port()
    if not port:
        print("❌ 无法找到可用端口")
        return
    
    print(f"✅ 找到可用端口: {port}")
    
    # 检查依赖
    try:
        import flask, pandas, openpyxl, numpy
        print("✅ 依赖包检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return
    
    # 创建目录
    for dir_name in ['uploads', 'exports']:
        os.makedirs(dir_name, exist_ok=True)
    
    # 启动应用
    try:
        from app import app
        print(f"🚀 启动应用...")
        print(f"📱 访问地址: http://localhost:{port}")
        print(f"🛑 按 Ctrl+C 停止服务")
        print("=" * 50)
        
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
