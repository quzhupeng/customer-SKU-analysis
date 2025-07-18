#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试成本率分析功能
Comprehensive test for cost rate analysis
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import DataAnalyzer

def create_comprehensive_test_data():
    """创建包含完整字段的测试数据"""
    
    # 创建包含所有必需字段的数据
    data = pd.DataFrame({
        '产品名称': [f'产品{i}' for i in range(20)],
        '销售金额': np.random.uniform(50, 200, 20),  # 销售金额
        '毛利': np.random.uniform(5, 50, 20),        # 毛利
        '数量': np.random.uniform(5, 50, 20),        # 数量
        '成本': np.random.uniform(30, 150, 20),      # 成本
        '海运费': np.random.uniform(1, 10, 20),      # 海运费
        '陆运费': np.random.uniform(0.5, 5, 20),     # 陆运费
        '代理费': np.random.uniform(0.2, 2, 20),     # 代理费
    })
    
    return data

def test_cost_rate_analysis():
    """测试成本率分析功能"""
    print("开始测试成本率分析功能...")
    
    # 创建测试数据
    data = create_comprehensive_test_data()
    
    # 保存到临时文件
    temp_file = "temp_cost_rate_test.xlsx"
    data.to_excel(temp_file, index=False, sheet_name='Sheet1')
    
    try:
        # 创建分析器
        analyzer = DataAnalyzer(temp_file, 'Sheet1')
        
        # 单位确认
        unit_confirmations = {
            'quantity': 't',
            'amount': 'wan_yuan'
        }
        
        # 执行分析
        print("执行产品分析...")
        result = analyzer.analyze('product', unit_confirmations)
        
        # 检查聚合数据
        aggregated_data_dict = result.get('aggregated_data', [])
        if aggregated_data_dict:
            # 转换回DataFrame进行检查
            import pandas as pd
            aggregated_df = pd.DataFrame(aggregated_data_dict)
            print(f"聚合数据字段: {list(aggregated_df.columns)}")

            # 检查聚合数据的成本数据检测
            has_cost_data_agg = analyzer._has_cost_data(aggregated_df)
            print(f"聚合数据成本检测结果: {has_cost_data_agg}")

        # 检查成本数据检测
        has_cost_data = analyzer._has_cost_data(analyzer.processed_data)
        print(f"处理数据成本检测结果: {has_cost_data}")

        # 检查结果结构
        print(f"分析结果包含的键: {list(result.keys())}")

        # 检查成本率分析结果 - 在additional_analysis中
        additional_analysis = result.get('additional_analysis', {})
        cost_analysis = additional_analysis.get('cost_analysis', {})
        print(f"成本分析结果: {bool(cost_analysis)}")

        if cost_analysis:
            print(f"成本分析包含的键: {list(cost_analysis.keys())}")

            # 检查成本率分布
            rate_distribution = cost_analysis.get('rate_distribution', {})
            if rate_distribution:
                division_methods = rate_distribution.get('division_methods', [])
                print(f"✅ 成本率分布分析成功")
                print(f"   划分方法数量: {len(division_methods)}")

                for method in division_methods:
                    method_name = method.get('method_name', 'Unknown')
                    intervals = method.get('intervals_info', {}).get('intervals', [])
                    print(f"   - {method_name}: {len(intervals)-1}个区间")
            else:
                print("❌ 没有成本率分布数据")
        
        if cost_analysis:
            rate_distribution = cost_analysis.get('rate_distribution', {})
            print(f"成本率分布结果: {bool(rate_distribution)}")
            
            if rate_distribution:
                division_methods = rate_distribution.get('division_methods', [])
                print(f"划分方法数量: {len(division_methods)}")
                
                # 显示详细信息
                avg_cost_rate = rate_distribution.get('avg_cost_rate', 0)
                median_cost_rate = rate_distribution.get('median_cost_rate', 0)
                print(f"平均成本率: {avg_cost_rate:.3f}")
                print(f"中位数成本率: {median_cost_rate:.3f}")
                
                # 显示每种划分方法
                for i, method in enumerate(division_methods):
                    method_name = method.get('method_name', 'Unknown')
                    intervals = method.get('intervals_info', {}).get('intervals', [])
                    labels = method.get('intervals_info', {}).get('labels', [])
                    print(f"  方法 {i+1}: {method_name}")
                    print(f"    区间: {intervals}")
                    print(f"    标签: {labels}")
                    
                    # 检查分布数据
                    dist_data = method.get('distribution_data', [])
                    print(f"    分布数据项数: {len(dist_data)}")
            else:
                print("❌ 没有成本率分布数据")
        else:
            print("❌ 没有成本分析数据")
            
        # 检查字段映射
        print(f"字段映射: {analyzer.field_mapping}")

        # 检查处理后的数据是否包含成本率
        processed_data = analyzer.processed_data
        if processed_data is not None:
            print(f"处理后数据的字段: {list(processed_data.columns)}")

            if '成本率' in processed_data.columns:
                cost_rates = processed_data['成本率']
                print(f"✅ 成本率计算成功")
                print(f"   成本率范围: {cost_rates.min():.3f} - {cost_rates.max():.3f}")
                print(f"   成本率平均值: {cost_rates.mean():.3f}")
                print(f"   成本率中位数: {cost_rates.median():.3f}")
                print(f"   有效成本率数量: {cost_rates.notna().sum()}")
            else:
                print("❌ 处理后的数据中没有成本率字段")

            # 检查是否有总成本字段
            if '总成本' in processed_data.columns:
                total_costs = processed_data['总成本']
                print(f"✅ 总成本计算成功")
                print(f"   总成本范围: {total_costs.min():.3f} - {total_costs.max():.3f}")
            else:
                print("❌ 处理后的数据中没有总成本字段")
        else:
            print("❌ 没有处理后的数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    """主函数"""
    print("=" * 60)
    print("成本率分析功能全面测试")
    print("=" * 60)
    
    success = test_cost_rate_analysis()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试完成！")
    else:
        print("❌ 测试失败！")
    print("=" * 60)

if __name__ == '__main__':
    main()
