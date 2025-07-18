#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试bins单调性修复
Test script for bins monotonicity fix
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import DataAnalyzer

def create_test_data():
    """创建测试数据，包含可能导致bins问题的情况"""
    
    # 情况1：所有成本率都相同
    data1 = pd.DataFrame({
        '产品名称': [f'产品{i}' for i in range(10)],
        '销售金额': np.random.uniform(10, 100, 10),
        '毛利': np.random.uniform(1, 10, 10),
        '数量': np.random.uniform(1, 20, 10),
        '成本': [50] * 10  # 所有成本都相同
    })
    
    # 情况2：成本率分布很集中
    data2 = pd.DataFrame({
        '产品名称': [f'产品{i}' for i in range(10)],
        '销售金额': np.random.uniform(10, 100, 10),
        '毛利': np.random.uniform(1, 10, 10),
        '数量': np.random.uniform(1, 20, 10),
        '成本': np.random.uniform(49, 51, 10)  # 成本很集中
    })
    
    # 情况3：极端值
    data3 = pd.DataFrame({
        '产品名称': [f'产品{i}' for i in range(10)],
        '销售金额': np.random.uniform(10, 100, 10),
        '毛利': np.random.uniform(1, 10, 10),
        '数量': np.random.uniform(1, 20, 10),
        '成本': [0, 0, 0, 100, 100, 100, 50, 50, 50, 50]  # 极端分布
    })
    
    # 情况4：正常分布
    data4 = pd.DataFrame({
        '产品名称': [f'产品{i}' for i in range(20)],
        '销售金额': np.random.uniform(10, 100, 20),
        '毛利': np.random.uniform(1, 10, 20),
        '数量': np.random.uniform(1, 20, 20),
        '成本': np.random.uniform(10, 90, 20)  # 正常分布
    })
    
    return [
        ("相同成本率", data1),
        ("集中分布", data2), 
        ("极端分布", data3),
        ("正常分布", data4)
    ]

def test_analyzer(name, data):
    """测试分析器"""
    print(f"\n{'='*50}")
    print(f"测试场景: {name}")
    print(f"{'='*50}")

    try:
        # 保存测试数据到临时Excel文件
        temp_file = f"temp_test_{name.replace(' ', '_')}.xlsx"
        data.to_excel(temp_file, index=False, sheet_name='Sheet1')

        # 创建分析器
        analyzer = DataAnalyzer(temp_file, 'Sheet1')

        # 单位确认
        unit_confirmations = {
            'quantity': 't',
            'amount': 'wan_yuan'
        }

        # 执行分析
        result = analyzer.analyze('product', unit_confirmations)

        # 清理临时文件
        import os
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        # 检查成本率分析结果
        cost_analysis = result.get('cost_analysis', {})
        rate_distribution = cost_analysis.get('rate_distribution', {})
        division_methods = rate_distribution.get('division_methods', [])
        
        print(f"✅ 分析成功完成")
        print(f"   - 成本率范围: {data['成本'].min():.1f} - {data['成本'].max():.1f}")
        if '成本率' in data.columns:
            print(f"   - 成本率范围: {data['成本率'].min():.3f} - {data['成本率'].max():.3f}")
        print(f"   - 划分方法数量: {len(division_methods)}")
        
        for method in division_methods:
            method_name = method.get('method_name', 'Unknown')
            intervals = method.get('intervals_info', {}).get('intervals', [])
            print(f"   - {method_name}: {len(intervals)-1}个区间")
            
        return True

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

        # 清理临时文件
        import os
        temp_file = f"temp_test_{name.replace(' ', '_')}.xlsx"
        if os.path.exists(temp_file):
            os.remove(temp_file)

        return False

def main():
    """主函数"""
    print("开始测试bins单调性修复...")
    
    test_cases = create_test_data()
    success_count = 0
    total_count = len(test_cases)
    
    for name, data in test_cases:
        if test_analyzer(name, data):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"测试总结")
    print(f"{'='*50}")
    print(f"成功: {success_count}/{total_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有测试通过！bins单调性问题已修复。")
    else:
        print("⚠️  仍有测试失败，需要进一步调试。")

if __name__ == '__main__':
    main()
