#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成本率分布图优化功能测试
Test script for cost rate distribution chart optimization
"""

import pandas as pd
import numpy as np
from analyzer import DataAnalyzer

def create_test_data():
    """创建测试数据"""
    np.random.seed(42)
    
    # 生成100个测试项目
    n_items = 100
    
    data = {
        'product_name': [f'产品{i:03d}' for i in range(1, n_items + 1)],
        'sales_amount': np.random.lognormal(mean=3, sigma=1, size=n_items) * 10,  # 销售额
        'quantity': np.random.lognormal(mean=2, sigma=0.8, size=n_items),  # 数量
        'material_cost': np.random.uniform(5, 50, n_items),  # 材料成本
        'sea_freight': np.random.uniform(1, 10, n_items),  # 海运费
        'land_freight': np.random.uniform(0.5, 5, n_items),  # 陆运费
        'agency_fee': np.random.uniform(0.2, 2, n_items),  # 代理费
    }
    
    df = pd.DataFrame(data)
    
    # 计算利润
    df['profit'] = df['sales_amount'] - (df['material_cost'] + df['sea_freight'] + 
                                        df['land_freight'] + df['agency_fee'])
    
    return df

def test_cost_rate_analysis():
    """测试成本率分析功能"""
    print("🧪 开始测试成本率分布图优化功能...")
    
    # 创建测试数据
    test_data = create_test_data()
    print(f"✅ 创建测试数据: {len(test_data)} 个项目")
    
    # 设置字段映射
    field_mapping = {
        'product': 'product_name',
        'amount': 'sales_amount',
        'quantity': 'quantity',
        'profit': 'profit',
        'cost': 'material_cost',
        'sea_freight': 'sea_freight',
        'land_freight': 'land_freight',
        'agency_fee': 'agency_fee'
    }
    
    # 创建分析器
    analyzer = DataAnalyzer(field_mapping)
    
    # 预处理数据
    processed_data = analyzer._preprocess_data(test_data)
    print(f"✅ 数据预处理完成，包含成本率字段: {'成本率' in processed_data.columns}")
    
    # 测试成本率分布分析
    try:
        cost_analysis = analyzer._cost_analysis(processed_data, 'product')
        rate_distribution = cost_analysis.get('rate_distribution', {})
        
        print(f"✅ 成本率分布分析完成")
        print(f"   - 平均成本率: {rate_distribution.get('avg_cost_rate', 0):.2%}")
        print(f"   - 中位数成本率: {rate_distribution.get('median_cost_rate', 0):.2%}")
        print(f"   - 划分方法数量: {len(rate_distribution.get('division_methods', []))}")
        
        # 测试价值字段
        value_fields = rate_distribution.get('value_fields', [])
        print(f"   - 支持的价值字段: {[f['name'] for f in value_fields]}")
        
        # 测试区间划分方法
        division_methods = rate_distribution.get('division_methods', [])
        for i, method in enumerate(division_methods):
            print(f"   - 划分方法 {i+1}: {method['method_name']} ({method['method_type']})")
            print(f"     区间数量: {len(method['distribution_data'])}")
        
        # 测试价值分布数据
        if division_methods:
            first_method = division_methods[0]
            value_distribution = first_method.get('value_distribution_data', {})
            print(f"   - 价值分布数据字段: {list(value_distribution.keys())}")
            
            # 检查利润字段的盈亏分布
            if 'profit' in value_distribution:
                profit_data = value_distribution['profit']
                has_profit_loss = any('profit_value' in item for item in profit_data)
                print(f"   - 利润盈亏分布支持: {has_profit_loss}")
        
        print("✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_data_structure():
    """测试数据结构完整性"""
    print("\n🔍 测试数据结构完整性...")
    
    test_data = create_test_data()
    field_mapping = {
        'product': 'product_name',
        'amount': 'sales_amount',
        'quantity': 'quantity',
        'profit': 'profit',
        'cost': 'material_cost',
        'sea_freight': 'sea_freight',
        'land_freight': 'land_freight',
        'agency_fee': 'agency_fee'
    }
    
    analyzer = DataAnalyzer(field_mapping)
    processed_data = analyzer._preprocess_data(test_data)
    
    # 测试成本率分布
    rate_distribution = analyzer._cost_rate_distribution(processed_data)
    
    # 验证必需字段
    required_fields = [
        'distribution_data', 'value_distribution_data', 'avg_cost_rate',
        'median_cost_rate', 'interval_details', 'division_methods', 'value_fields'
    ]
    
    missing_fields = [field for field in required_fields if field not in rate_distribution]
    if missing_fields:
        print(f"❌ 缺少必需字段: {missing_fields}")
        return False
    
    # 验证division_methods结构
    division_methods = rate_distribution['division_methods']
    if not division_methods:
        print("❌ 没有划分方法")
        return False
    
    for method in division_methods:
        required_method_fields = [
            'method_name', 'method_type', 'description', 'distribution_data',
            'value_distribution_data', 'interval_details'
        ]
        missing_method_fields = [field for field in required_method_fields if field not in method]
        if missing_method_fields:
            print(f"❌ 划分方法缺少字段: {missing_method_fields}")
            return False
    
    print("✅ 数据结构完整性验证通过！")
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("成本率分布图优化功能测试")
    print("=" * 60)
    
    # 运行测试
    test1_passed = test_cost_rate_analysis()
    test2_passed = test_data_structure()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！成本率分布图优化功能正常工作。")
    else:
        print("❌ 部分测试失败，请检查代码。")
    print("=" * 60)
