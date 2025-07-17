#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试盈亏分析逻辑
"""

import pandas as pd
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_profit_loss_logic():
    """测试盈亏分析逻辑"""
    
    # 创建测试数据，模拟春雪小酥肉的情况
    test_data = pd.DataFrame({
        '产品名称': ['春雪小酥肉', '其他产品A', '其他产品B'],
        '毛利': [-2.3688, 1.5, -0.8],  # 万元
        '数量': [9.423, 10.0, 5.0],    # 吨
        '销售金额': [10.0, 15.0, 8.0]  # 万元
    })
    
    # 计算吨毛利
    test_data['吨毛利'] = (test_data['毛利'] / test_data['数量'] * 10000).fillna(0)
    
    print("测试数据:")
    print(test_data)
    print()
    
    # 测试使用总毛利的分类
    print("使用总毛利分类:")
    profitable_by_total = test_data[test_data['毛利'] > 0]
    loss_by_total = test_data[test_data['毛利'] <= 0]
    print(f"盈利项目 (总毛利>0): {len(profitable_by_total)} 个")
    print(profitable_by_total[['产品名称', '毛利', '吨毛利']])
    print(f"亏损项目 (总毛利<=0): {len(loss_by_total)} 个")
    print(loss_by_total[['产品名称', '毛利', '吨毛利']])
    print()
    
    # 测试使用吨毛利的分类
    print("使用吨毛利分类:")
    profitable_by_ton = test_data[test_data['吨毛利'] > 0]
    loss_by_ton = test_data[test_data['吨毛利'] <= 0]
    print(f"盈利项目 (吨毛利>0): {len(profitable_by_ton)} 个")
    print(profitable_by_ton[['产品名称', '毛利', '吨毛利']])
    print(f"亏损项目 (吨毛利<=0): {len(loss_by_ton)} 个")
    print(loss_by_ton[['产品名称', '毛利', '吨毛利']])
    print()
    
    # 检查春雪小酥肉的分类
    chunxue_row = test_data[test_data['产品名称'] == '春雪小酥肉'].iloc[0]
    print("春雪小酥肉详细信息:")
    print(f"  毛利: {chunxue_row['毛利']} 万元")
    print(f"  吨毛利: {chunxue_row['吨毛利']} 元/吨")
    print(f"  按总毛利分类: {'盈利' if chunxue_row['毛利'] > 0 else '亏损'}")
    print(f"  按吨毛利分类: {'盈利' if chunxue_row['吨毛利'] > 0 else '亏损'}")

if __name__ == '__main__':
    test_profit_loss_logic()
