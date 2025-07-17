#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
Utility Functions Module

Author: Augment Agent
Date: 2025-07-15
"""

import os
import re
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename: str) -> bool:
    """
    检查文件扩展名是否被允许
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否允许的文件类型
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder(folder_path: str) -> None:
    """
    创建上传文件夹（如果不存在）
    
    Args:
        folder_path: 文件夹路径
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def clean_column_name(column_name: str) -> str:
    """
    清理列名，去除多余的空格和特殊字符

    Args:
        column_name: 原始列名

    Returns:
        str: 清理后的列名
    """
    if column_name is None:
        return ''

    if not isinstance(column_name, str):
        column_name = str(column_name)

    # 去除前后空格
    cleaned = column_name.strip()

    # 将多个连续空格替换为单个空格，但保留必要的空格
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned

def get_field_aliases() -> Dict[str, List[str]]:
    """
    获取字段别名映射
    按优先级排序，优先级高的在前面
    
    Returns:
        Dict[str, List[str]]: 字段别名映射
    """
    return {
        'product': ['SKU', '物料名称', '产品名称', '存货名称', '物料', '单品', '产品', '商品', '货品', '品名', '物料编码', '产品编码', '商品名称', '货物名称', '品种', '产品型号', '型号', '规格'],
        'customer': ['客户名称', '客户', '客户全称', '客户简称', '购买方', '买方', '采购方', '客户代码', '客户编码', '客户ID', '买家', '收货方', '收货人', '终端客户', '最终客户'],
        'region': ['地区', '区域', '省份', '地域', '区域名称', '省市', '城市', '省', '市', '地区名称', '销售区域', '配送区域'],
        'quantity': ['数量', '销量', '销售数量', '出货量', '发货量', '重量', '净重', '毛重', '吨数', '件数', '箱数', '包装数量', '发货数量', '出库数量'],
        'profit': ['毛利', '利润', '毛利润', '毛利额', '利润额', '盈利', '毛利金额', '利润金额', '毛利贡献', '利润贡献'],
        'amount': ['金额', '销售额', '含税金额', '销售金额', '总金额', '成交金额', '交易金额', '订单金额', '合同金额', '开票金额', '收入', '营业额'],
        'cost': ['成本', '成本价', '采购成本', '进货成本', '单位成本', '总成本', '成本金额'],
        'sea_freight': ['海运费', '海运成本', '海运费用', '海运运费'],
        'land_freight': ['陆运费', '陆运成本', '陆运费用', '运费', '运输费', '物流费', '配送费'],
        'agency_fee': ['代办费', '代理费', '服务费', '手续费', '佣金', '促销管理费', '仓储费'],
        'unit_price': ['单价', '价格', '售价', '单位价格', '含税单价', '不含税单价'],
        'category': ['物料基本分类', '分类', '类别', '产品分类', '商品分类', '品类', '产品类型', '商品类型']
    }

def detect_field_type(column_name: str) -> str:
    """
    根据列名检测字段类型

    Args:
        column_name: 列名

    Returns:
        str: 字段类型，如果未识别则返回'unknown'
    """
    cleaned_name = clean_column_name(column_name)
    aliases = get_field_aliases()

    # 首先进行精确匹配
    for field_type, alias_list in aliases.items():
        if cleaned_name in alias_list:
            return field_type

    # 如果精确匹配失败，进行模糊匹配
    for field_type, alias_list in aliases.items():
        for alias in alias_list:
            # 检查是否包含关键词
            if alias in cleaned_name or cleaned_name in alias:
                return field_type

    # 特殊处理一些常见的变体和关键字
    special_patterns = {
        'product': ['品', '料', 'sku', 'SKU', '物料', '产品', '商品', '货品'],
        'customer': ['客', '户', '买', '购', '收货'],
        'region': ['地', '区', '省', '市', '域'],
        'quantity': ['量', '数', '重', '吨', '件', '箱'],
        'profit': ['利', '润', '盈'],
        'amount': ['额', '金', '收入', '营业'],
        'cost': ['本', '价', '成本'],
        'unit_price': ['价', '单价', '价格']
    }

    # 更灵活的模糊匹配
    for field_type, patterns in special_patterns.items():
        for pattern in patterns:
            if pattern in cleaned_name:
                return field_type

    # 最后尝试更宽松的匹配
    loose_patterns = {
        'customer': ['客户', '买方', '购买', '收货'],
        'product': ['产品', '商品', '物料', '货品'],
        'region': ['地区', '区域', '省份'],
        'amount': ['金额', '销售', '收入'],
        'quantity': ['数量', '销量', '重量'],
        'profit': ['毛利', '利润']
    }

    for field_type, patterns in loose_patterns.items():
        for pattern in patterns:
            if pattern in cleaned_name or any(p in cleaned_name for p in pattern):
                return field_type

    return 'unknown'

def validate_required_fields(detected_fields: Dict[str, str], analysis_type: str) -> List[str]:
    """
    验证必需字段是否存在

    Args:
        detected_fields: 检测到的字段映射
        analysis_type: 分析类型 ('product', 'customer', 'region')

    Returns:
        List[str]: 缺失的必需字段列表
    """
    # 更灵活的字段要求：只需要核心字段和至少一个数值字段
    core_fields = {
        'product': 'product',    # 产品分析：需要产品名
        'customer': 'customer',  # 客户分析：需要客户名
        'region': 'region'       # 地区分析：需要地区名
    }

    # 数值字段：至少需要其中一个
    value_fields = ['quantity', 'profit', 'amount']

    missing_fields = []

    # 检查核心字段
    core_field = core_fields.get(analysis_type)
    if core_field and (core_field not in detected_fields or not detected_fields[core_field]):
        missing_fields.append(core_field)

    # 检查是否有至少一个数值字段
    has_value_field = any(field in detected_fields and detected_fields[field] for field in value_fields)
    if not has_value_field:
        missing_fields.extend([field for field in value_fields if field not in detected_fields])

    return missing_fields

def get_unit_options() -> Dict[str, List[Dict[str, Any]]]:
    """
    获取单位选项配置
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: 单位选项配置
    """
    return {
        'quantity': [
            {'value': 'kg', 'label': '千克(kg)', 'default': True},
            {'value': 't', 'label': '吨(t)', 'default': False}
        ],
        'amount': [
            {'value': 'yuan', 'label': '元', 'default': True},
            {'value': 'wan_yuan', 'label': '万元', 'default': False}
        ]
    }

def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """
    单位转换
    
    Args:
        value: 原始值
        from_unit: 原始单位
        to_unit: 目标单位
        
    Returns:
        float: 转换后的值
    """
    # 重量单位转换
    if from_unit == 'kg' and to_unit == 't':
        return value / 1000
    elif from_unit == 't' and to_unit == 'kg':
        return value * 1000
    
    # 金额单位转换
    elif from_unit == 'yuan' and to_unit == 'wan_yuan':
        return value / 10000
    elif from_unit == 'wan_yuan' and to_unit == 'yuan':
        return value * 10000
    
    # 相同单位或不支持的转换
    return value

def format_number(value: float, decimal_places: int = 2) -> str:
    """
    格式化数字显示
    
    Args:
        value: 数值
        decimal_places: 小数位数
        
    Returns:
        str: 格式化后的字符串
    """
    if value is None or pd.isna(value):
        return "0"
    
    try:
        return f"{float(value):,.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(value)

def calculate_quadrant(x_value: float, y_value: float, x_avg: float, y_avg: float) -> int:
    """
    计算象限位置（按标准笛卡尔坐标系逆时针编号）

    Args:
        x_value: X轴值
        y_value: Y轴值
        x_avg: X轴平均值
        y_avg: Y轴平均值

    Returns:
        int: 象限编号 (1-4)
    """
    if x_value >= x_avg and y_value >= y_avg:
        return 1  # 第一象限：高X，高Y (明星产品)
    elif x_value < x_avg and y_value >= y_avg:
        return 2  # 第二象限：低X，高Y (潜力产品)
    elif x_value < x_avg and y_value < y_avg:
        return 3  # 第三象限：低X，低Y (瘦狗产品)
    else:
        return 4  # 第四象限：高X，低Y (金牛产品)

def get_quadrant_info(analysis_type: str) -> Dict[int, Dict[str, str]]:
    """
    获取象限信息配置
    
    Args:
        analysis_type: 分析类型
        
    Returns:
        Dict[int, Dict[str, str]]: 象限信息配置
    """
    quadrant_configs = {
        'product': {
            1: {
                'name': '明星产品',
                'description': '高毛利, 高销量',
                'strategy': '重点保护与投入，保证产能、优先备货、加大营销'
            },
            2: {
                'name': '潜力产品',
                'description': '高毛利, 低销量',
                'strategy': '精准营销与试错，分析销量低的原因'
            },
            3: {
                'name': '瘦狗产品',
                'description': '低毛利, 低销量',
                'strategy': '简化或淘汰，评估战略保留价值'
            },
            4: {
                'name': '金牛产品',
                'description': '低毛利, 高销量',
                'strategy': '优化成本与关联销售，审视生产流程，利用其流量'
            }
        },
        'customer': {
            1: {
                'name': '核心客户',
                'description': '高金额, 高毛利',
                'strategy': '战略合作，VIP服务，高层互访，建立长期护城河'
            },
            2: {
                'name': '成长客户',
                'description': '低金额, 高毛利',
                'strategy': '扶持与渗透，销售重点跟进，增加其采购份额和频次'
            },
            3: {
                'name': '机会客户',
                'description': '低金额, 低毛利',
                'strategy': '标准化服务，降低服务成本，不投入过多资源'
            },
            4: {
                'name': '增利客户',
                'description': '高金额, 低毛利',
                'strategy': '提升利润，引导采购高利润产品，审视折扣'
            }
        },
        'region': {
            1: {
                'name': '核心市场',
                'description': '高金额, 高毛利',
                'strategy': '重点投入资源，建立区域壁垒，可作为新产品首发试点'
            },
            2: {
                'name': '机会市场',
                'description': '低金额, 高毛利',
                'strategy': '精准定位高价值客户，加强市场渗透'
            },
            3: {
                'name': '边缘市场',
                'description': '低金额, 低毛利',
                'strategy': '维持最低成本运营，标准化服务，定期复评'
            },
            4: {
                'name': '规模市场',
                'description': '高金额, 低毛利',
                'strategy': '优化物流和渠道成本，引导销售高毛利产品组合'
            }
        }
    }
    
    return quadrant_configs.get(analysis_type, {})

def safe_to_dict(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    安全地将DataFrame转换为字典列表，处理NaN值

    Args:
        df: 要转换的DataFrame

    Returns:
        List[Dict[str, Any]]: 转换后的字典列表
    """
    # 将NaN值替换为None，这样可以被JSON序列化
    df_clean = df.replace({np.nan: None, np.inf: None, -np.inf: None})

    # 转换为字典列表
    records = df_clean.to_dict('records')

    # 进一步清理数据，确保所有值都可以JSON序列化
    cleaned_records = []
    for record in records:
        cleaned_record = {}
        for key, value in record.items():
            if pd.isna(value) or value is np.nan:
                cleaned_record[key] = None
            elif isinstance(value, (np.integer, np.floating)):
                # 转换numpy数值类型为Python原生类型
                if np.isfinite(value):
                    cleaned_record[key] = float(value) if isinstance(value, np.floating) else int(value)
                else:
                    cleaned_record[key] = None
            else:
                cleaned_record[key] = value
        cleaned_records.append(cleaned_record)

    return cleaned_records
