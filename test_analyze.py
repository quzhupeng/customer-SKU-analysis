#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分析功能
Test Analysis Functionality
"""

import os
import json

def test_full_analysis():
    """测试完整的分析流程"""
    print("=" * 50)
    print("测试完整分析流程")
    print("=" * 50)
    
    try:
        from analyzer import DataAnalyzer
        
        # 测试示例数据
        if not os.path.exists('示例数据.xlsx'):
            print("❌ 示例数据文件不存在")
            return False
        
        # 测试分单品分析
        print("\n📦 测试分单品分析...")
        analyzer = DataAnalyzer('示例数据.xlsx', '分单品')
        
        # 字段检测
        fields = analyzer.detect_fields()
        print(f"✓ 检测到字段: {list(fields['detected_fields'].keys())}")
        
        # 验证字段
        validation = analyzer.validate_fields('product')
        if not validation['is_valid']:
            print(f"❌ 字段验证失败: {validation['missing_fields']}")
            return False
        print("✓ 字段验证通过")
        
        # 执行分析
        unit_confirmations = {
            'quantity': 'kg',
            'amount': 'yuan'
        }
        
        result = analyzer.analyze('product', unit_confirmations)
        print("✓ 分单品分析完成")
        print(f"  - 聚合数据: {len(result['aggregated_data'])} 条")
        print(f"  - 四象限数据: {len(result['quadrant_analysis']['scatter_data'])} 个点")
        
        # 测试分客户分析
        print("\n👥 测试分客户分析...")
        analyzer2 = DataAnalyzer('示例数据.xlsx', '分客户')
        result2 = analyzer2.analyze('customer', unit_confirmations)
        print("✓ 分客户分析完成")
        
        # 测试分地区分析
        print("\n🗺️ 测试分地区分析...")
        analyzer3 = DataAnalyzer('示例数据.xlsx', '分地区')
        result3 = analyzer3.analyze('region', unit_confirmations)
        print("✓ 分地区分析完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 50)
    print("测试API端点")
    print("=" * 50)
    
    try:
        import requests
        base_url = 'http://localhost:8080'
        
        # 测试主页
        print("🏠 测试主页...")
        response = requests.get(f'{base_url}/')
        if response.status_code == 200:
            print("✓ 主页访问正常")
        else:
            print(f"❌ 主页访问失败: {response.status_code}")
            return False
        
        # 测试文件上传（空请求）
        print("📤 测试上传接口...")
        response = requests.post(f'{base_url}/upload')
        if response.status_code == 400:
            result = response.json()
            if '没有选择文件' in result.get('error', ''):
                print("✓ 上传接口正常（预期错误）")
            else:
                print(f"⚠️ 上传接口响应异常: {result}")
        else:
            print(f"❌ 上传接口测试失败: {response.status_code}")
        
        # 测试字段检测（空请求）
        print("🔍 测试字段检测接口...")
        response = requests.post(f'{base_url}/field_detection', 
                               json={},
                               headers={'Content-Type': 'application/json'})
        if response.status_code == 400:
            result = response.json()
            if '缺少必要参数' in result.get('error', ''):
                print("✓ 字段检测接口正常（预期错误）")
            else:
                print(f"⚠️ 字段检测接口响应异常: {result}")
        else:
            print(f"❌ 字段检测接口测试失败: {response.status_code}")
        
        # 测试分析接口（空请求）
        print("📊 测试分析接口...")
        response = requests.post(f'{base_url}/analyze',
                               json={},
                               headers={'Content-Type': 'application/json'})
        if response.status_code == 400:
            result = response.json()
            if '缺少必要参数' in result.get('error', ''):
                print("✓ 分析接口正常（预期错误）")
            else:
                print(f"⚠️ 分析接口响应异常: {result}")
        else:
            print(f"❌ 分析接口测试失败: {response.status_code}")
        
        return True
        
    except ImportError:
        print("⚠️ 需要安装requests库: pip install requests")
        return False
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def main():
    print("🧪 产品客户价值分析系统 - 全面测试")
    
    # 测试分析功能
    analysis_ok = test_full_analysis()
    
    # 测试API端点
    api_ok = test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    if analysis_ok:
        print("✅ 分析功能测试通过")
    else:
        print("❌ 分析功能测试失败")
    
    if api_ok:
        print("✅ API接口测试通过")
    else:
        print("❌ API接口测试失败")
    
    if analysis_ok and api_ok:
        print("\n🎉 所有测试通过！应用可以正常使用。")
        print("\n📱 访问地址: http://localhost:8080")
        print("📁 使用示例数据.xlsx进行测试")
    else:
        print("\n⚠️ 部分测试失败，请检查相关问题。")

if __name__ == '__main__':
    main()
