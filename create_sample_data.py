#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建示例数据文件
Create Sample Data File
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def create_sample_product_data():
    """创建分单品分析示例数据"""
    
    # 产品列表
    products = [
        '钢材A', '钢材B', '钢材C', '钢材D', '钢材E',
        '铝材A', '铝材B', '铝材C', '铜材A', '铜材B',
        '塑料A', '塑料B', '塑料C', '橡胶A', '橡胶B',
        '化工A', '化工B', '化工C', '建材A', '建材B'
    ]
    
    # 客户列表
    customers = [
        '华东建设集团', '中南钢铁公司', '北方制造厂', '西部工业园',
        '东海化工厂', '南山建材公司', '长江钢铁厂', '黄河制造公司',
        '珠江工业集团', '渤海建设公司', '太湖制造厂', '洞庭工业园'
    ]
    
    # 地区列表
    regions = ['华东', '华南', '华北', '华中', '西南', '西北', '东北']
    
    # 生成随机数据
    np.random.seed(42)  # 固定随机种子以便复现
    random.seed(42)
    
    data = []
    
    for _ in range(500):  # 生成500条记录
        record = {
            '物料名称': random.choice(products),
            '客户名称': random.choice(customers),
            '地区': random.choice(regions),
            '数量': round(np.random.exponential(20) + 1, 2),  # 指数分布，平均20kg
            '单价': round(np.random.normal(5000, 1000), 2),  # 正态分布，平均5000元/吨
            '金额': 0,  # 稍后计算
            '成本': 0,  # 稍后计算
            '毛利': 0,  # 稍后计算
            '海运费': round(np.random.uniform(100, 500), 2),
            '陆运费': round(np.random.uniform(50, 200), 2),
            '代办费': round(np.random.uniform(20, 100), 2),
        }
        
        # 计算衍生字段
        record['金额'] = round(record['数量'] * record['单价'] / 1000, 2)  # 转换为万元
        
        # 成本率在60%-90%之间
        cost_rate = np.random.uniform(0.6, 0.9)
        record['成本'] = round(record['金额'] * cost_rate, 2)
        
        # 毛利 = 金额 - 成本 - 各种费用
        total_fees = (record['海运费'] + record['陆运费'] + record['代办费']) / 10000  # 转换为万元
        record['毛利'] = round(record['金额'] - record['成本'] - total_fees, 2)
        
        data.append(record)
    
    return pd.DataFrame(data)

def create_sample_customer_data():
    """创建分客户分析示例数据"""
    
    # 基于产品数据生成客户汇总数据
    product_data = create_sample_product_data()
    
    # 按客户聚合
    customer_data = product_data.groupby(['客户名称', '地区']).agg({
        '数量': 'sum',
        '金额': 'sum',
        '成本': 'sum',
        '毛利': 'sum',
        '海运费': 'sum',
        '陆运费': 'sum',
        '代办费': 'sum'
    }).reset_index()
    
    return customer_data

def create_sample_region_data():
    """创建分地区分析示例数据"""
    
    # 基于产品数据生成地区汇总数据
    product_data = create_sample_product_data()
    
    # 按地区聚合
    region_data = product_data.groupby('地区').agg({
        '数量': 'sum',
        '金额': 'sum',
        '成本': 'sum',
        '毛利': 'sum',
        '海运费': 'sum',
        '陆运费': 'sum',
        '代办费': 'sum'
    }).reset_index()
    
    # 添加客户数量
    customer_counts = product_data.groupby('地区')['客户名称'].nunique().reset_index()
    customer_counts.columns = ['地区', '客户数量']
    region_data = region_data.merge(customer_counts, on='地区')
    
    return region_data

def main():
    """主函数"""
    print("创建示例数据文件...")
    
    # 创建Excel文件
    with pd.ExcelWriter('示例数据.xlsx', engine='openpyxl') as writer:
        
        # 分单品数据
        product_data = create_sample_product_data()
        product_data.to_excel(writer, sheet_name='分单品', index=False)
        print(f"✓ 分单品数据: {len(product_data)} 条记录")
        
        # 分客户数据
        customer_data = create_sample_customer_data()
        customer_data.to_excel(writer, sheet_name='分客户', index=False)
        print(f"✓ 分客户数据: {len(customer_data)} 条记录")
        
        # 分地区数据
        region_data = create_sample_region_data()
        region_data.to_excel(writer, sheet_name='分地区', index=False)
        print(f"✓ 分地区数据: {len(region_data)} 条记录")
    
    print("\n示例数据文件已创建: 示例数据.xlsx")
    print("\n数据字段说明:")
    print("- 物料名称: 产品名称")
    print("- 客户名称: 客户名称")
    print("- 地区: 销售地区")
    print("- 数量: 销售数量(kg)")
    print("- 单价: 单价(元/吨)")
    print("- 金额: 销售金额(万元)")
    print("- 成本: 成本(万元)")
    print("- 毛利: 毛利(万元)")
    print("- 海运费/陆运费/代办费: 各项费用(元)")
    
    print("\n可以使用此文件测试系统的各种分析功能。")

if __name__ == '__main__':
    main()
