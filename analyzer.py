#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析核心模块
Data Analysis Core Module

Author: Augment Agent
Date: 2025-07-15
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging
from utils import (
    get_field_aliases, detect_field_type, validate_required_fields,
    convert_units, calculate_quadrant, get_quadrant_info,
    safe_to_dict
)

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """数据分析器类"""
    
    def __init__(self, filepath: str, sheet_name: str):
        """
        初始化数据分析器
        
        Args:
            filepath: Excel文件路径
            sheet_name: 工作表名称
        """
        self.filepath = filepath
        self.sheet_name = sheet_name
        self.raw_data = None
        self.processed_data = None
        self.field_mapping = {}
        self.unit_confirmations = {}
        
        # 加载数据
        self._load_data()
    
    def _load_data(self) -> None:
        """加载Excel数据"""
        try:
            self.raw_data = pd.read_excel(self.filepath, sheet_name=self.sheet_name)

            # 检查数据是否为空
            if self.raw_data.empty:
                raise ValueError(f"工作表 '{self.sheet_name}' 中没有数据")

            # 清理列名
            self.raw_data.columns = [str(col).strip() if col is not None else f'未命名列_{i}'
                                   for i, col in enumerate(self.raw_data.columns)]

            logger.info(f"成功加载数据，共{len(self.raw_data)}行，{len(self.raw_data.columns)}列")

        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
            raise
    
    def detect_fields(self) -> Dict[str, Any]:
        """
        检测字段映射
        
        Returns:
            Dict[str, Any]: 字段检测结果
        """
        if self.raw_data is None:
            raise ValueError("数据未加载")
        
        detected_fields = {}
        column_info = {}
        
        # 获取字段别名映射
        aliases = get_field_aliases()
        
        # 检测每个列的字段类型
        for column in self.raw_data.columns:
            try:
                field_type = detect_field_type(column)

                # 安全地获取样本值
                try:
                    sample_values = self.raw_data[column].dropna().head(3).tolist()
                    # 确保样本值可以序列化
                    sample_values = [str(val) if not isinstance(val, (str, int, float, bool)) else val
                                   for val in sample_values]
                except Exception:
                    sample_values = []

                column_info[column] = {
                    'field_type': field_type,
                    'data_type': str(self.raw_data[column].dtype),
                    'non_null_count': int(self.raw_data[column].count()),
                    'sample_values': sample_values
                }
            except Exception as e:
                logger.warning(f"处理列 '{column}' 时出错: {str(e)}")
                column_info[column] = {
                    'field_type': 'unknown',
                    'data_type': 'unknown',
                    'non_null_count': 0,
                    'sample_values': []
                }
            
            # 如果检测到已知字段类型，记录映射
            if field_type != 'unknown':
                if field_type not in detected_fields:
                    detected_fields[field_type] = column
                else:
                    # 如果有冲突，选择优先级更高的
                    current_column = detected_fields[field_type]
                    try:
                        current_priority = aliases[field_type].index(current_column)
                    except (ValueError, KeyError):
                        current_priority = 999

                    try:
                        new_priority = aliases[field_type].index(column)
                    except (ValueError, KeyError):
                        new_priority = 999

                    if new_priority < current_priority:
                        detected_fields[field_type] = column
        
        self.field_mapping = detected_fields
        
        return {
            'detected_fields': detected_fields,
            'column_info': column_info,
            'total_rows': len(self.raw_data),
            'total_columns': len(self.raw_data.columns)
        }
    
    def validate_fields(self, analysis_type: str) -> Dict[str, Any]:
        """
        验证字段完整性
        
        Args:
            analysis_type: 分析类型
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        missing_fields = validate_required_fields(self.field_mapping, analysis_type)
        
        return {
            'is_valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'detected_fields': self.field_mapping
        }
    
    def _apply_unit_conversions(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        应用单位转换
        
        Args:
            data: 原始数据
            
        Returns:
            pd.DataFrame: 转换后的数据
        """
        converted_data = data.copy()
        
        # 数量单位转换
        if 'quantity' in self.field_mapping and 'quantity' in self.unit_confirmations:
            quantity_col = self.field_mapping['quantity']
            from_unit = self.unit_confirmations['quantity']
            
            if from_unit == 'kg':
                # 转换为吨
                converted_data[quantity_col] = converted_data[quantity_col].apply(
                    lambda x: convert_units(x, 'kg', 't') if pd.notna(x) else x
                )
        
        # 金额单位转换
        amount_fields = ['profit', 'amount']
        for field in amount_fields:
            if field in self.field_mapping and 'amount' in self.unit_confirmations:
                amount_col = self.field_mapping[field]
                from_unit = self.unit_confirmations['amount']
                
                if from_unit == 'yuan':
                    # 转换为万元
                    converted_data[amount_col] = converted_data[amount_col].apply(
                        lambda x: convert_units(x, 'yuan', 'wan_yuan') if pd.notna(x) else x
                    )
        
        return converted_data
    
    def _calculate_derived_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算衍生指标
        
        Args:
            data: 数据
            
        Returns:
            pd.DataFrame: 包含衍生指标的数据
        """
        result_data = data.copy()
        
        # 计算吨毛利（元/吨）
        if 'quantity' in self.field_mapping and 'profit' in self.field_mapping:
            quantity_col = self.field_mapping['quantity']
            profit_col = self.field_mapping['profit']
            
            # 吨毛利 = 毛利 / 数量 * 10000 (因为毛利是万元，数量是吨)
            result_data['吨毛利'] = (result_data[profit_col] / result_data[quantity_col] * 10000).fillna(0)
        
        # 计算总成本
        cost_fields = ['cost', 'sea_freight', 'land_freight', 'agency_fee']
        cost_columns = []
        
        for field in cost_fields:
            if field in self.field_mapping:
                cost_columns.append(self.field_mapping[field])
        
        if cost_columns:
            result_data['总成本'] = result_data[cost_columns].fillna(0).sum(axis=1)
            
            # 计算成本率（限制在合理范围内）
            if 'amount' in self.field_mapping:
                amount_col = self.field_mapping['amount']
                # 计算成本率，避免除零错误，并限制在合理范围内
                cost_rate = result_data['总成本'] / result_data[amount_col].replace(0, np.nan)
                result_data['成本率'] = cost_rate.fillna(0).clip(0, 10)  # 限制成本率在0-10之间（1000%）
        
        return result_data
    
    def _aggregate_data(self, data: pd.DataFrame, analysis_type: str) -> pd.DataFrame:
        """
        数据聚合
        
        Args:
            data: 处理后的数据
            analysis_type: 分析类型
            
        Returns:
            pd.DataFrame: 聚合后的数据
        """
        # 确定分组字段
        group_field_map = {
            'product': 'product',
            'customer': 'customer', 
            'region': 'region'
        }
        
        group_field = group_field_map[analysis_type]
        if group_field not in self.field_mapping:
            raise ValueError(f"缺少{group_field}字段")
        
        group_column = self.field_mapping[group_field]
        
        # 定义聚合规则
        agg_rules = {}
        
        # 基础聚合字段
        if 'quantity' in self.field_mapping:
            agg_rules[self.field_mapping['quantity']] = 'sum'
        
        if 'profit' in self.field_mapping:
            agg_rules[self.field_mapping['profit']] = 'sum'
        
        if 'amount' in self.field_mapping:
            agg_rules[self.field_mapping['amount']] = 'sum'
        
        # 成本相关字段
        cost_fields = ['cost', 'sea_freight', 'land_freight', 'agency_fee']
        for field in cost_fields:
            if field in self.field_mapping:
                agg_rules[self.field_mapping[field]] = 'sum'
        
        if '总成本' in data.columns:
            agg_rules['总成本'] = 'sum'
        
        # 执行聚合
        aggregated = data.groupby(group_column).agg(agg_rules).reset_index()
        
        # 重新计算衍生指标
        if 'quantity' in self.field_mapping and 'profit' in self.field_mapping:
            quantity_col = self.field_mapping['quantity']
            profit_col = self.field_mapping['profit']
            aggregated['吨毛利'] = (aggregated[profit_col] / aggregated[quantity_col] * 10000).fillna(0)
        
        if '总成本' in aggregated.columns and 'amount' in self.field_mapping:
            amount_col = self.field_mapping['amount']
            # 计算成本率，避免除零错误，并限制在合理范围内
            cost_rate = aggregated['总成本'] / aggregated[amount_col].replace(0, np.nan)
            aggregated['成本率'] = cost_rate.fillna(0).clip(0, 10)  # 限制成本率在0-10之间（1000%）
        
        return aggregated

    def _perform_quadrant_analysis(self, data: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """
        执行四象限分析

        Args:
            data: 聚合后的数据
            analysis_type: 分析类型

        Returns:
            Dict[str, Any]: 四象限分析结果
        """
        # 确定X轴和Y轴字段
        axis_config = {
            'product': {
                'x_field': 'quantity',  # 销量(吨)
                'y_field': '吨毛利',     # 吨毛利(元/吨)
                'x_label': '销量(吨)',
                'y_label': '吨毛利(元/吨)'
            },
            'customer': {
                'x_field': 'amount',    # 销售金额(万元)
                'y_field': 'profit',    # 毛利贡献(万元)
                'x_label': '销售金额(万元)',
                'y_label': '毛利贡献(万元)'
            },
            'region': {
                'x_field': 'amount',    # 地区销售金额(万元)
                'y_field': 'profit',    # 地区毛利贡献(万元)
                'x_label': '地区销售金额(万元)',
                'y_label': '地区毛利贡献(万元)'
            }
        }

        config = axis_config[analysis_type]

        # 获取实际列名
        if config['x_field'] == '吨毛利':
            x_column = '吨毛利'
        else:
            if config['x_field'] not in self.field_mapping:
                raise ValueError(f"缺少必需的X轴字段: {config['x_field']}")
            x_column = self.field_mapping[config['x_field']]

        if config['y_field'] == '吨毛利':
            y_column = '吨毛利'
        else:
            if config['y_field'] not in self.field_mapping:
                raise ValueError(f"缺少必需的Y轴字段: {config['y_field']}")
            y_column = self.field_mapping[config['y_field']]

        # 检查列是否存在于数据中
        if x_column not in data.columns:
            raise ValueError(f"数据中缺少X轴列: {x_column}")
        if y_column not in data.columns:
            raise ValueError(f"数据中缺少Y轴列: {y_column}")

        # 计算平均值作为分割线
        x_avg = data[x_column].mean()

        # 对于按单品分析的吨毛利，需要特殊计算平均值
        if analysis_type == 'product' and config['y_field'] == '吨毛利':
            # 吨毛利平均值 = 毛利总和 / 数量总和 * 1000 (因为毛利是万元，数量是吨，转换为元/吨)
            if 'profit' in self.field_mapping and 'quantity' in self.field_mapping:
                profit_col = self.field_mapping['profit']
                quantity_col = self.field_mapping['quantity']
                total_profit = data[profit_col].sum()
                total_quantity = data[quantity_col].sum()
                if total_quantity > 0:
                    y_avg = (total_profit / total_quantity) * 10000  # 万元转元，所以是10000而不是1000
                else:
                    y_avg = data[y_column].mean()
            else:
                y_avg = data[y_column].mean()
        else:
            y_avg = data[y_column].mean()

        # 为每个数据点分配象限
        data['象限'] = data.apply(
            lambda row: calculate_quadrant(row[x_column], row[y_column], x_avg, y_avg),
            axis=1
        )

        # 获取象限信息
        quadrant_info = get_quadrant_info(analysis_type)

        # 为每个数据点添加象限名称
        data['象限名称'] = data['象限'].map(lambda q: quadrant_info[q]['name'])

        # 计算总体统计数据
        total_count = len(data)
        total_profit = data[self.field_mapping['profit']].sum() if 'profit' in self.field_mapping else 0
        total_amount = data[self.field_mapping['amount']].sum() if 'amount' in self.field_mapping else 0

        # 统计各象限数据
        quadrant_stats = {}
        for quadrant in [1, 2, 3, 4]:
            quadrant_data = data[data['象限'] == quadrant]
            count = len(quadrant_data)

            # 计算各种占比和数量
            count_percentage = (count / total_count * 100) if total_count > 0 else 0

            # 毛利贡献统计
            profit_sum = quadrant_data[self.field_mapping['profit']].sum() if 'profit' in self.field_mapping else 0
            profit_percentage = (profit_sum / total_profit * 100) if total_profit > 0 else 0

            # 销售额统计
            amount_sum = quadrant_data[self.field_mapping['amount']].sum() if 'amount' in self.field_mapping else 0
            amount_percentage = (amount_sum / total_amount * 100) if total_amount > 0 else 0

            # 数量统计（用于按单品分析）
            quantity_sum = quadrant_data[self.field_mapping['quantity']].sum() if 'quantity' in self.field_mapping else 0
            total_quantity = data[self.field_mapping['quantity']].sum() if 'quantity' in self.field_mapping else 0
            quantity_percentage = (quantity_sum / total_quantity * 100) if total_quantity > 0 else 0

            # 吨毛利计算（用于按单品分析）- 特殊计算方式
            ton_profit = 0
            if analysis_type == 'product' and 'profit' in self.field_mapping and 'quantity' in self.field_mapping:
                if quantity_sum > 0:
                    ton_profit = (profit_sum / quantity_sum) * 10000  # 万元转元/吨

            quadrant_stats[quadrant] = {
                'name': quadrant_info[quadrant]['name'],
                'description': quadrant_info[quadrant]['description'],
                'strategy': quadrant_info[quadrant]['strategy'],
                'count': count,
                'count_percentage': round(count_percentage, 0),
                'profit_sum': round(profit_sum, 0),
                'profit_percentage': round(profit_percentage, 0),
                'amount_sum': round(amount_sum, 0),
                'amount_percentage': round(amount_percentage, 0),
                'quantity_sum': round(quantity_sum, 0),
                'quantity_percentage': round(quantity_percentage, 0),
                'ton_profit': round(ton_profit, 0),
                'items': safe_to_dict(quadrant_data)
            }

# Ensure the group field is included in scatter data output
        group_column = self._get_group_column(analysis_type)
        scatter_data_output = safe_to_dict(data)
        for item in scatter_data_output:
            # Add the group field explicitly to each item
            if group_column in data.columns:
                # Find the corresponding row in the original data to get the group value
                matching_rows = data[data.index == item.get('index', -1)]
                if not matching_rows.empty:
                    item['group'] = matching_rows.iloc[0][group_column]
                elif group_column in item:
                    item['group'] = item[group_column]
                else:
                    # 如果找不到匹配的行，尝试直接从item中获取group_column的值
                    if group_column in item:
                        item['group'] = item[group_column]
                    else:
                        # 最后尝试使用index作为group
                        item['group'] = item.get('index', str(item))

        return {
            'scatter_data': scatter_data_output,
            'x_avg': x_avg,
            'y_avg': y_avg,
            'x_label': config['x_label'],
            'y_label': config['y_label'],
            'quadrant_stats': quadrant_stats
        }

    def _perform_additional_analysis(self, data: pd.DataFrame, analysis_type: str, pareto_dimension: str = None) -> Dict[str, Any]:
        """
        执行额外的分析（帕累托、分布等）

        Args:
            data: 聚合后的数据
            analysis_type: 分析类型
            pareto_dimension: 帕累托分析维度

        Returns:
            Dict[str, Any]: 额外分析结果
        """
        results = {}

        # 1. 帕累托分析
        results['pareto_analysis'] = self._pareto_analysis(data, analysis_type, pareto_dimension)

        # 2. 分布区间分析
        results['distribution_analysis'] = self._distribution_analysis(data, analysis_type)

        # 3. 盈亏分析
        results['profit_loss_analysis'] = self._profit_loss_analysis(data, analysis_type)

        # 4. 贡献度分析
        results['contribution_analysis'] = self._contribution_analysis(data, analysis_type)

        # 5. 成本分析（如果有成本数据）
        if self._has_cost_data(data):
            results['cost_analysis'] = self._cost_analysis(data, analysis_type)

        return results

    def _pareto_analysis(self, data: pd.DataFrame, analysis_type: str, pareto_dimension: str = None) -> Dict[str, Any]:
        """
        帕累托分析（80/20法则）

        Args:
            data: 聚合后的数据
            analysis_type: 分析类型 ('product', 'customer', 'region')
            pareto_dimension: 帕累托分析维度 ('profit', 'amount', 'quantity')

        Returns:
            Dict[str, Any]: 帕累托分析结果
        """
        # 如果没有指定维度，使用默认维度
        if pareto_dimension is None:
            default_dimension_map = {
                'product': 'profit',  # 单品默认按毛利排序
                'customer': 'amount',  # 客户默认按采购金额排序
                'region': 'amount'    # 地区默认按销售金额排序
            }
            pareto_dimension = default_dimension_map[analysis_type]

        # 验证维度是否可用
        available_dimensions = self._get_available_pareto_dimensions(analysis_type)
        if pareto_dimension not in available_dimensions:
            # 如果指定维度不可用，使用第一个可用维度
            pareto_dimension = available_dimensions[0] if available_dimensions else 'profit'

        # 获取排序字段
        if pareto_dimension not in self.field_mapping:
            raise ValueError(f"缺少帕累托分析所需字段: {pareto_dimension}")
        sort_column = self.field_mapping[pareto_dimension]

        # 按指定字段降序排序
        sorted_data = data.sort_values(sort_column, ascending=False).reset_index(drop=True)

        # 计算累计值和累计占比
        total_value = sorted_data[sort_column].sum()
        sorted_data['累计值'] = sorted_data[sort_column].cumsum()
        sorted_data['累计占比'] = (sorted_data['累计值'] / total_value * 100).round(2)

        # 找到80%的分界点
        pareto_80_index = sorted_data[sorted_data['累计占比'] <= 80].index.max()
        if pd.isna(pareto_80_index):
            pareto_80_index = 0

        # 核心项目（贡献80%的项目）
        core_items = sorted_data.iloc[:pareto_80_index + 1]

        # 获取维度标签和单位
        dimension_info = self._get_pareto_dimension_info(pareto_dimension, analysis_type)

        return {
            'pareto_data': safe_to_dict(sorted_data),
            'core_items': safe_to_dict(core_items),
            'core_items_count': len(core_items),
            'core_items_percentage': round(len(core_items) / len(sorted_data) * 100, 2),
            'total_items': len(sorted_data),
            'dimension': pareto_dimension,
            'dimension_info': dimension_info,
            'available_dimensions': available_dimensions
        }

    def _get_available_pareto_dimensions(self, analysis_type: str) -> List[str]:
        """
        获取可用的帕累托分析维度

        Args:
            analysis_type: 分析类型

        Returns:
            List[str]: 可用维度列表
        """
        # 基础维度配置
        base_dimensions = {
            'product': ['profit', 'quantity'],  # 单品：毛利、销量
            'customer': ['amount', 'profit', 'quantity'],  # 客户：金额、毛利、销量
            'region': ['amount', 'profit', 'quantity']     # 地区：金额、毛利、销量
        }

        # 获取该分析类型的基础维度
        dimensions = base_dimensions.get(analysis_type, ['profit', 'amount', 'quantity'])

        # 过滤出实际可用的维度（存在于字段映射中）
        available = []
        for dim in dimensions:
            if dim in self.field_mapping:
                available.append(dim)

        return available

    def _get_pareto_dimension_info(self, dimension: str, analysis_type: str) -> Dict[str, str]:
        """
        获取帕累托分析维度的显示信息

        Args:
            dimension: 维度名称
            analysis_type: 分析类型

        Returns:
            Dict[str, str]: 维度信息
        """
        # 维度标签映射
        dimension_labels = {
            'profit': {
                'product': {'name': '毛利', 'unit': '万元', 'description': '按产品毛利贡献排序'},
                'customer': {'name': '毛利贡献', 'unit': '万元', 'description': '按客户毛利贡献排序'},
                'region': {'name': '毛利贡献', 'unit': '万元', 'description': '按地区毛利贡献排序'}
            },
            'amount': {
                'product': {'name': '销售金额', 'unit': '万元', 'description': '按产品销售金额排序'},
                'customer': {'name': '采购金额', 'unit': '万元', 'description': '按客户采购金额排序'},
                'region': {'name': '销售金额', 'unit': '万元', 'description': '按地区销售金额排序'}
            },
            'quantity': {
                'product': {'name': '销量', 'unit': '吨', 'description': '按产品销量排序'},
                'customer': {'name': '采购量', 'unit': '吨', 'description': '按客户采购量排序'},
                'region': {'name': '销量', 'unit': '吨', 'description': '按地区销量排序'}
            }
        }

        # 获取维度信息
        if dimension in dimension_labels and analysis_type in dimension_labels[dimension]:
            return dimension_labels[dimension][analysis_type]
        else:
            # 默认信息
            return {
                'name': dimension,
                'unit': '',
                'description': f'按{dimension}排序'
            }

    def _distribution_analysis(self, data: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """分布区间分析 - 升级版：提供双指标统计和价值维度分析"""
        # 根据分析类型定义区间配置
        interval_configs = {
            'product': {
                'primary_field': 'quantity',  # 主要分组字段
                'value_field': 'amount',      # 价值字段
                'intervals': [0, 5, 10, 20, 50, float('inf')],
                'labels': ['<5吨', '5-10吨', '10-20吨', '20-50吨', '>50吨'],
                'title': '销量分布区间分析',
                'primary_label': '销量(吨)',
                'value_label': '销售金额(万元)'
            },
            'customer': {
                'primary_field': 'amount',
                'value_field': 'amount',      # 对于客户分析，采购金额既是分组字段也是价值字段
                'intervals': [0, 10, 50, 100, 500, float('inf')],
                'labels': ['<10万', '10-50万', '50-100万', '100-500万', '>500万'],
                'title': '采购金额分布区间分析',
                'primary_label': '采购金额(万元)',
                'value_label': '采购金额(万元)'
            },
            'region': {
                'primary_field': 'amount',
                'value_field': 'amount',
                'intervals': [0, 50, 200, 500, 1000, float('inf')],
                'labels': ['<50万', '50-200万', '200-500万', '500-1000万', '>1000万'],
                'title': '销售金额分布区间分析',
                'primary_label': '销售金额(万元)',
                'value_label': '销售金额(万元)'
            }
        }

        config = interval_configs[analysis_type]

        # 检查必需字段
        if config['primary_field'] not in self.field_mapping:
            raise ValueError(f"缺少分布分析所需字段: {config['primary_field']}")
        if config['value_field'] not in self.field_mapping:
            raise ValueError(f"缺少分布分析所需字段: {config['value_field']}")

        primary_column = self.field_mapping[config['primary_field']]
        value_column = self.field_mapping[config['value_field']]

        # 创建区间分组，添加错误处理
        try:
            data['区间'] = pd.cut(data[primary_column],
                               bins=config['intervals'],
                               labels=config['labels'],
                               right=False)
        except ValueError as e:
            print(f"分布区间分析失败: {e}")
            print(f"字段: {primary_column}")
            print(f"数据范围: {data[primary_column].min()} - {data[primary_column].max()}")
            print(f"区间: {config['intervals']}")
            raise ValueError(f"分布区间分析失败: {e}")

        # 双指标统计：数量统计 + 价值统计
        if config['primary_field'] == config['value_field']:
            # 当主要字段和价值字段相同时（如客户分析），只对一个字段进行聚合
            interval_stats = data.groupby('区间', observed=False).agg({
                primary_column: ['count', 'sum', 'mean']
            }).round(2)
            interval_stats.columns = ['项目数量', '价值总和', '价值平均']
        else:
            # 当主要字段和价值字段不同时（如产品分析），对两个字段分别聚合
            interval_stats = data.groupby('区间', observed=False).agg({
                primary_column: ['count', 'sum', 'mean'],
                value_column: ['sum', 'mean']
            }).round(2)
            interval_stats.columns = ['项目数量', '主要指标总和', '主要指标平均', '价值总和', '价值平均']

        # 处理空区间的NaN值
        interval_stats = interval_stats.fillna(0)

        # 计算百分比
        total_count = len(data)
        total_value = data[value_column].sum()

        interval_stats['数量占比'] = (interval_stats['项目数量'] / total_count * 100).round(1)
        interval_stats['价值占比'] = (interval_stats['价值总和'] / total_value * 100).round(1)

        # 计算平均价值（价值总和 / 项目数量），避免除零错误
        interval_stats['单项平均价值'] = interval_stats.apply(
            lambda row: round(row['价值总和'] / row['项目数量'], 2) if row['项目数量'] > 0 else 0,
            axis=1
        )

        # 重置索引以便转换为字典
        interval_stats_reset = interval_stats.reset_index()

        # 为每个区间添加详细项目列表（用于下钻功能）
        interval_details = {}
        group_column = self._get_group_column(analysis_type)

        for interval_name in config['labels']:
            interval_data = data[data['区间'] == interval_name]
            if not interval_data.empty:
                # 获取该区间的所有项目详情
                items = []
                for _, row in interval_data.iterrows():
                    item = {
                        'name': row[group_column],
                        'primary_value': round(row[primary_column], 2),
                        'value': round(row[value_column], 2)
                    }
                    # 添加其他有用字段
                    if 'profit' in self.field_mapping:
                        item['profit'] = round(row[self.field_mapping['profit']], 2)
                    items.append(item)

                # 按价值降序排序
                items.sort(key=lambda x: x['value'], reverse=True)
                interval_details[interval_name] = items
            else:
                # 为空区间也创建空列表，保持数据结构一致性
                interval_details[interval_name] = []

        return {
            'title': config['title'],
            'primary_label': config['primary_label'],
            'value_label': config['value_label'],
            'interval_data': safe_to_dict(interval_stats_reset),
            'interval_details': interval_details,
            'total_count': total_count,
            'total_value': round(total_value, 2),
            'analysis_summary': {
                'highest_count_interval': interval_stats_reset.loc[interval_stats_reset['项目数量'].idxmax(), '区间'],
                'highest_value_interval': interval_stats_reset.loc[interval_stats_reset['价值总和'].idxmax(), '区间'],
                'avg_value_per_item': round(total_value / total_count, 2)
            },
            'raw_data_with_intervals': safe_to_dict(data)
        }

    def _profit_loss_analysis(self, data: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """盈亏分析"""
        if 'profit' not in self.field_mapping:
            raise ValueError("缺少盈亏分析所需的毛利字段")
        profit_column = self.field_mapping['profit']

        # 根据分析类型选择合适的盈亏判断标准
        if analysis_type == 'product' and '吨毛利' in data.columns:
            # 对于产品分析，使用吨毛利作为盈亏判断标准，与四象限分析保持一致
            profit_criterion_column = '吨毛利'
        else:
            # 对于客户和地区分析，使用总毛利作为判断标准
            profit_criterion_column = profit_column

        # 分离盈利和亏损数据
        profitable = data[data[profit_criterion_column] > 0]
        loss_making = data[data[profit_criterion_column] <= 0]

        # 强制调试：将信息写入文件
        import os
        debug_file = os.path.join(os.path.dirname(__file__), 'profit_loss_debug.txt')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(f"=== 盈亏分析调试信息 ===\n")
            f.write(f"分析类型: {analysis_type}\n")
            f.write(f"判断字段: {profit_criterion_column}\n")
            f.write(f"数据总数: {len(data)}\n")
            f.write(f"盈利项目数: {len(profitable)}\n")
            f.write(f"亏损项目数: {len(loss_making)}\n")

            # 查找包含"春雪"或"小酥肉"的产品
            group_col = self._get_group_column(analysis_type)
            chunxue_mask = data[group_col].str.contains('春雪|小酥肉', na=False, case=False)
            if chunxue_mask.any():
                f.write("找到春雪相关产品:\n")
                for idx, row in data[chunxue_mask].iterrows():
                    product_name = row[group_col]
                    criterion_value = row[profit_criterion_column]
                    profit_value = row[profit_column]
                    is_profitable = criterion_value > 0
                    f.write(f"  - {product_name}: {profit_criterion_column}={criterion_value}, 毛利={profit_value}, 分类={'盈利' if is_profitable else '亏损'}\n")
            else:
                f.write("未找到春雪相关产品，显示前5个产品:\n")
                for idx, row in data.head(5).iterrows():
                    product_name = row[group_col]
                    criterion_value = row[profit_criterion_column]
                    profit_value = row[profit_column]
                    is_profitable = criterion_value > 0
                    f.write(f"  - {product_name}: {profit_criterion_column}={criterion_value}, 毛利={profit_value}, 分类={'盈利' if is_profitable else '亏损'}\n")
            f.write("========================\n")

        # 统计信息
        total_count = len(data)
        profitable_count = len(profitable)
        loss_count = len(loss_making)

        profitable_percentage = round(profitable_count / total_count * 100, 2) if total_count > 0 else 0
        loss_percentage = round(loss_count / total_count * 100, 2) if total_count > 0 else 0

        # 盈亏金额统计 - 始终使用总毛利进行金额统计，但分类使用对应的标准
        total_profit = profitable[profit_column].sum() if len(profitable) > 0 else 0
        total_loss = abs(loss_making[profit_column].sum()) if len(loss_making) > 0 else 0
        net_profit = total_profit - total_loss

# Ensure the group field is included in profit/loss item output
        group_column = self._get_group_column(analysis_type)
        profitable_output = safe_to_dict(profitable)
        loss_making_output = safe_to_dict(loss_making)

        # Add group field to profitable items
        for item in profitable_output:
            if group_column in profitable.columns:
                # Find the corresponding row to get the group value
                matching_rows = profitable[profitable.index == item.get('index', -1)]
                if not matching_rows.empty:
                    item['group'] = matching_rows.iloc[0][group_column]
                elif group_column in item:
                    item['group'] = item[group_column]
                else:
                    # 如果找不到匹配的行，尝试直接从item中获取group_column的值
                    if group_column in item:
                        item['group'] = item[group_column]
                    else:
                        # 最后尝试使用index作为group
                        item['group'] = item.get('index', str(item))

        # Add group field to loss-making items
        for item in loss_making_output:
            if group_column in loss_making.columns:
                # Find the corresponding row to get the group value
                matching_rows = loss_making[loss_making.index == item.get('index', -1)]
                if not matching_rows.empty:
                    item['group'] = matching_rows.iloc[0][group_column]
                elif group_column in item:
                    item['group'] = item[group_column]
                else:
                    # 如果找不到匹配的行，尝试直接从item中获取group_column的值
                    if group_column in item:
                        item['group'] = item[group_column]
                    else:
                        # 最后尝试使用index作为group
                        item['group'] = item.get('index', str(item))

        return {
            'summary': {
                'total_count': total_count,
                'profitable_count': profitable_count,
                'loss_count': loss_count,
                'profitable_percentage': profitable_percentage,
                'loss_percentage': loss_percentage,
                'total_profit': round(total_profit, 2),
                'total_loss': round(total_loss, 2),
                'net_profit': round(net_profit, 2)
            },
            'profitable_items': profitable_output,
            'loss_making_items': loss_making_output
        }

    def _contribution_analysis(self, data: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """贡献度分析"""
        # 根据分析类型选择分析字段
        analysis_fields = {
            'product': ['quantity', 'profit', 'amount'],
            'customer': ['amount', 'profit', 'quantity'],
            'region': ['amount', 'profit', 'quantity']
        }

        fields = analysis_fields[analysis_type]
        contribution_data = {}

        for field in fields:
            if field in self.field_mapping:
                column = self.field_mapping[field]
                total_value = data[column].sum()

                # 计算每项的贡献度
                data[f'{field}_contribution'] = (data[column] / total_value * 100).round(2)

                # 排序并获取前10名
                top_contributors = data.nlargest(10, column)

                contribution_data[field] = {
                    'total_value': round(total_value, 2),
                    'top_contributors': safe_to_dict(top_contributors)
                }

        return contribution_data

    def analyze(self, analysis_type: str, unit_confirmations: Dict[str, str], pareto_dimension: str = None) -> Dict[str, Any]:
        """
        执行完整的数据分析

        Args:
            analysis_type: 分析类型 ('product', 'customer', 'region')
            unit_confirmations: 单位确认信息
            pareto_dimension: 帕累托分析维度 ('profit', 'amount', 'quantity')

        Returns:
            Dict[str, Any]: 完整的分析结果
        """
        self.unit_confirmations = unit_confirmations

        # 1. 检测字段
        field_detection = self.detect_fields()

        # 2. 验证字段
        field_validation = self.validate_fields(analysis_type)
        if not field_validation['is_valid']:
            raise ValueError(f"缺少必需字段: {field_validation['missing_fields']}")

        # 3. 数据预处理
        processed_data = self._apply_unit_conversions(self.raw_data)
        processed_data = self._calculate_derived_metrics(processed_data)

        # 保存处理后的数据到实例属性
        self.processed_data = processed_data

        # 4. 数据聚合
        aggregated_data = self._aggregate_data(processed_data, analysis_type)

        # 5. 四象限分析
        quadrant_analysis = self._perform_quadrant_analysis(aggregated_data, analysis_type)

        # 6. 其他分析（帕累托、分布等）
        additional_analysis = self._perform_additional_analysis(aggregated_data, analysis_type, pareto_dimension)

        return {
            'field_detection': field_detection,
            'field_validation': field_validation,
            'raw_data_info': {
                'total_rows': len(self.raw_data),
                'total_columns': len(self.raw_data.columns)
            },
            'processed_data': safe_to_dict(processed_data),
            'aggregated_data': safe_to_dict(aggregated_data),
            'quadrant_analysis': quadrant_analysis,
            'additional_analysis': additional_analysis,
            'analysis_type': analysis_type,
            'unit_confirmations': unit_confirmations
        }

    def _has_cost_data(self, data: pd.DataFrame) -> bool:
        """检查是否有成本相关数据"""
        cost_fields = ['cost', 'sea_freight', 'land_freight', 'agency_fee']
        has_cost_fields = any(field in self.field_mapping for field in cost_fields)
        has_total_cost = '总成本' in data.columns or '总成本(万元)' in data.columns
        has_cost_rate = '成本率' in data.columns

        return has_cost_fields or has_total_cost or has_cost_rate

    def _cost_analysis(self, data: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """成本分析"""
        cost_analysis = {}

        # 1. 成本构成分析
        cost_analysis['composition'] = self._cost_composition_analysis(data)

        # 2. 成本率分布分析
        if '成本率' in data.columns:
            cost_analysis['rate_distribution'] = self._cost_rate_distribution(data)

        # 3. 成本效率分析
        cost_analysis['efficiency'] = self._cost_efficiency_analysis(data, analysis_type)

        return cost_analysis

    def _cost_composition_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """成本构成分析"""
        cost_fields = {
            'cost': '基础成本',
            'sea_freight': '海运费',
            'land_freight': '陆运费',
            'agency_fee': '代办费'
        }

        composition_data = []
        total_cost = 0

        for field_key, field_name in cost_fields.items():
            if field_key in self.field_mapping:
                field_column = self.field_mapping[field_key]
                if field_column in data.columns:
                    field_sum = data[field_column].sum()
                    composition_data.append({
                        'name': field_name,
                        'value': field_sum,
                        'field': field_key
                    })
                    total_cost += field_sum

        # 计算占比
        for item in composition_data:
            item['percentage'] = (item['value'] / total_cost * 100) if total_cost > 0 else 0

        return {
            'composition_data': composition_data,
            'total_cost': total_cost
        }

    def _cost_rate_distribution(self, data: pd.DataFrame) -> Dict[str, Any]:
        """成本率分布分析 - 升级版：支持多维度价值分析和动态区间划分"""
        cost_rates = data['成本率'].dropna()

        if len(cost_rates) == 0:
            return {
                'distribution_data': [],
                'value_distribution_data': [],
                'avg_cost_rate': 0,
                'median_cost_rate': 0,
                'interval_details': {},
                'division_methods': []
            }

        # 获取可用的价值字段
        value_fields = self._get_available_value_fields(data)

        # 动态计算区间：支持多种划分方法
        intervals_config = self._calculate_dynamic_intervals(cost_rates)

        # 为每种区间划分方法生成数据
        division_methods = []
        for method_name, intervals_data in intervals_config.items():
            intervals = intervals_data['intervals']
            labels = intervals_data['labels']

            # 创建区间分组，添加错误处理
            try:
                cost_rate_intervals = pd.cut(cost_rates, bins=intervals, labels=labels, right=False, include_lowest=True)
            except ValueError as e:
                print(f"区间划分失败 ({method_name}): {e}")
                print(f"区间: {intervals}")
                print(f"成本率范围: {cost_rates.min()} - {cost_rates.max()}")
                continue  # 跳过这个划分方法

            # 统计各区间的多维度数据
            distribution_data, value_distribution_data, interval_details = self._calculate_interval_statistics(
                data, cost_rate_intervals, value_fields, intervals_data['method_type']
            )

            division_methods.append({
                'method_name': method_name,
                'method_type': intervals_data['method_type'],
                'description': intervals_data['description'],
                'distribution_data': distribution_data,
                'value_distribution_data': value_distribution_data,
                'interval_details': interval_details,
                'intervals_info': {
                    'intervals': intervals,
                    'labels': labels,
                    'range': f'{cost_rates.min():.1%} - {cost_rates.max():.1%}'
                }
            })

        # 如果没有生成任何划分方法，创建一个默认的
        if not division_methods:
            # 创建一个简单的默认划分
            default_intervals = [0, 0.5, 1.0]
            default_labels = ['<50%', '≥50%']

            try:
                # 调整默认区间以适应实际数据范围
                min_rate = cost_rates.min()
                max_rate = cost_rates.max()

                if min_rate >= 0.5:
                    # 如果所有数据都大于50%，调整区间
                    mid_point = (min_rate + max_rate) / 2
                    adjusted_intervals = [max(0, min_rate - 0.001), mid_point, min(1.0, max_rate + 0.001)]
                    adjusted_labels = ['低成本率', '高成本率']
                else:
                    adjusted_intervals = default_intervals
                    adjusted_labels = default_labels

                cost_rate_intervals = pd.cut(cost_rates, bins=adjusted_intervals, labels=adjusted_labels, right=False, include_lowest=True)
                distribution_data, value_distribution_data, interval_details = self._calculate_interval_statistics(
                    data, cost_rate_intervals, value_fields, 'default'
                )

                division_methods.append({
                    'method_name': '默认划分',
                    'method_type': 'default',
                    'description': '简单的二分法划分',
                    'distribution_data': distribution_data,
                    'value_distribution_data': value_distribution_data,
                    'interval_details': interval_details,
                    'intervals_info': {
                        'intervals': default_intervals,
                        'labels': default_labels,
                        'range': f'{cost_rates.min():.1%} - {cost_rates.max():.1%}'
                    }
                })
            except Exception as e:
                print(f"创建默认划分失败: {e}")
                # 如果连默认划分都失败，返回空数据
                return {
                    'distribution_data': [],
                    'value_distribution_data': {field['key']: [] for field in value_fields},
                    'avg_cost_rate': float(cost_rates.mean()),
                    'median_cost_rate': float(cost_rates.median()),
                    'interval_details': {},
                    'division_methods': [],
                    'value_fields': value_fields,
                    'intervals_info': {}
                }

        # 默认使用第一种方法
        default_method = division_methods[0]

        return {
            'distribution_data': default_method['distribution_data'],
            'value_distribution_data': default_method['value_distribution_data'],
            'avg_cost_rate': float(cost_rates.mean()),
            'median_cost_rate': float(cost_rates.median()),
            'interval_details': default_method['interval_details'],
            'division_methods': division_methods,
            'value_fields': value_fields,
            'intervals_info': default_method.get('intervals_info', {})
        }

    def _get_available_value_fields(self, data: pd.DataFrame):
        """获取可用的价值字段配置"""
        value_fields = [
            {
                'key': 'count',
                'name': '项目数量',
                'unit': '个',
                'description': '落入该成本率区间的项目数量'
            }
        ]

        # 销售额字段
        if 'amount' in self.field_mapping:
            value_fields.append({
                'key': 'amount',
                'name': '销售额总和',
                'unit': '万元',
                'description': '该区间内所有项目的销售额总和',
                'column': self.field_mapping['amount']
            })

        # 利润字段
        if 'profit' in self.field_mapping:
            value_fields.append({
                'key': 'profit',
                'name': '利润总和',
                'unit': '万元',
                'description': '该区间内所有项目的利润总和',
                'column': self.field_mapping['profit']
            })

        # 总成本字段
        if '总成本' in data.columns:
            value_fields.append({
                'key': 'total_cost',
                'name': '总成本',
                'unit': '万元',
                'description': '该区间内所有项目的总成本',
                'column': '总成本'
            })

        return value_fields

    def _calculate_dynamic_intervals(self, cost_rates: pd.Series):
        """计算多种动态区间划分方法"""
        min_rate = cost_rates.min()
        max_rate = cost_rates.max()

        intervals_config = {}

        # 1. 等频划分（四分位数）- 推荐方法
        if max_rate - min_rate >= 0.01:  # 降低阈值，数据范围足够大
            try:
                q25 = cost_rates.quantile(0.25)
                q50 = cost_rates.quantile(0.50)
                q75 = cost_rates.quantile(0.75)

                # 构建初始区间，确保包含数据范围
                intervals = [max(0, min_rate - 0.001), q25, q50, q75, min(1.0, max_rate + 0.001)]

                # 去重并排序，确保严格递增
                intervals = sorted(list(set(intervals)))

                # 验证区间是否严格递增且有足够的区间数
                if len(intervals) >= 3 and self._validate_intervals(intervals):
                    labels = self._generate_interval_labels(intervals)
                    intervals_config['等频划分（推荐）'] = {
                        'intervals': intervals,
                        'labels': labels,
                        'method_type': 'quartile',
                        'description': '基于四分位数划分，确保每个区间包含大致相同数量的项目'
                    }
            except Exception as e:
                print(f"等频划分失败: {e}")

        # 2. 等宽划分
        try:
            if max_rate - min_rate > 0:  # 确保有数据范围
                interval_width = (max_rate - min_rate) / 5  # 分为5个等宽区间
                intervals = [min_rate + i * interval_width for i in range(6)]

                # 调整边界，确保覆盖所有数据
                intervals[0] = max(0, min_rate - 0.001)  # 起始点略小于最小值
                intervals[-1] = min(1.0, max_rate + 0.001)  # 结束点略大于最大值

                # 验证区间
                if self._validate_intervals(intervals):
                    labels = self._generate_interval_labels(intervals)
                    intervals_config['等宽划分'] = {
                        'intervals': intervals,
                        'labels': labels,
                        'method_type': 'equal_width',
                        'description': '将成本率范围均匀分为5个等宽区间'
                    }
        except Exception as e:
            print(f"等宽划分失败: {e}")

        # 3. 标准区间（原有的固定区间）- 只有在数据范围合适时使用
        try:
            # 检查标准区间是否适合当前数据
            if min_rate >= 0 and max_rate <= 1.0:
                standard_intervals = [0, 0.3, 0.5, 0.7, 0.8, 1.0]
                standard_labels = ['<30%', '30-50%', '50-70%', '70-80%', '>80%']
                intervals_config['标准区间'] = {
                    'intervals': standard_intervals,
                    'labels': standard_labels,
                    'method_type': 'standard',
                    'description': '使用标准的成本率区间划分'
                }
            elif max_rate > 1.0:
                # 对于成本率超过100%的情况，使用扩展区间
                if max_rate <= 2.0:
                    extended_intervals = [0, 0.5, 1.0, max(2.1, max_rate + 0.1)]
                    extended_labels = ['<50%', '50-100%', f'>100%']
                else:
                    extended_intervals = [0, 0.5, 1.0, 2.0, max(10.0, max_rate + 0.1)]
                    extended_labels = ['<50%', '50-100%', '100-200%', f'>200%']

                intervals_config['扩展区间'] = {
                    'intervals': extended_intervals,
                    'labels': extended_labels,
                    'method_type': 'extended',
                    'description': '适用于高成本率数据的扩展区间划分'
                }
        except Exception as e:
            print(f"标准/扩展区间划分失败: {e}")

        # 如果所有方法都失败，创建一个简单的二分法
        if not intervals_config:
            try:
                mid_point = (min_rate + max_rate) / 2
                # 确保区间边界合理
                start_point = max(0, min_rate - 0.001)
                end_point = max_rate + 0.001

                simple_intervals = [start_point, mid_point, end_point]
                simple_labels = ['低成本率', '高成本率']

                intervals_config['简单划分'] = {
                    'intervals': simple_intervals,
                    'labels': simple_labels,
                    'method_type': 'simple',
                    'description': '简单的二分法划分'
                }
            except Exception as e:
                print(f"简单划分也失败: {e}")
                # 最后的保险措施 - 使用数据实际范围
                try:
                    safe_max = max(1.0, max_rate + 0.1)
                    intervals_config['默认划分'] = {
                        'intervals': [0, safe_max/2, safe_max],
                        'labels': ['低成本率', '高成本率'],
                        'method_type': 'default',
                        'description': '默认的二分法划分'
                    }
                except Exception:
                    # 绝对最后的保险措施
                    intervals_config['默认划分'] = {
                        'intervals': [0, 0.5, 1.0],
                        'labels': ['<50%', '≥50%'],
                        'method_type': 'default',
                        'description': '默认的二分法划分'
                    }

        # 如果等频划分失败，将第一个可用方法设为推荐
        if '等频划分（推荐）' not in intervals_config and intervals_config:
            first_method_key = list(intervals_config.keys())[0]
            first_method = intervals_config[first_method_key]
            intervals_config = {f'{first_method_key}（推荐）': first_method} | intervals_config
            intervals_config[f'{first_method_key}（推荐）']['description'] = '数据分布情况下的推荐划分方法'
            del intervals_config[first_method_key]

        return intervals_config

    def _validate_intervals(self, intervals):
        """验证区间是否严格递增且适合pandas.cut使用"""
        try:
            # 检查是否严格递增
            for i in range(1, len(intervals)):
                if intervals[i] <= intervals[i-1]:
                    return False

            # 检查是否有足够的区间（至少2个区间需要3个边界点）
            if len(intervals) < 3:
                return False

            # 检查数值是否有效（不是NaN或无穷大）
            for interval in intervals:
                if pd.isna(interval) or not np.isfinite(interval):
                    return False

            return True
        except Exception:
            return False

    def _generate_interval_labels(self, intervals):
        """生成区间标签"""
        labels = []
        for i in range(len(intervals) - 1):
            start_pct = int(intervals[i] * 100)
            end_pct = int(intervals[i + 1] * 100)
            if i == len(intervals) - 2:  # 最后一个区间
                labels.append(f'>{start_pct}%')
            else:
                labels.append(f'{start_pct}-{end_pct}%')
        return labels

    def _calculate_interval_statistics(self, data: pd.DataFrame, cost_rate_intervals: pd.Series,
                                     value_fields, method_type: str):
        """计算区间统计数据，支持多维度价值分析"""
        interval_stats = cost_rate_intervals.value_counts().sort_index()
        group_column = self._get_group_column('product')

        distribution_data = []
        value_distribution_data = {}
        interval_details = {}

        # 初始化价值分布数据结构
        for field in value_fields:
            value_distribution_data[field['key']] = []

        for interval, count in interval_stats.items():
            interval_name = str(interval)
            interval_mask = cost_rate_intervals == interval
            interval_data = data[interval_mask]

            # 基础分布数据（项目数量）
            distribution_item = {
                'interval': interval_name,
                'count': int(count),
                'percentage': round(count / len(cost_rate_intervals) * 100, 2)
            }
            distribution_data.append(distribution_item)

            # 价值维度分布数据
            for field in value_fields:
                if field['key'] == 'count':
                    # 项目数量
                    value_item = {
                        'interval': interval_name,
                        'value': int(count),
                        'percentage': round(count / len(cost_rate_intervals) * 100, 2)
                    }
                else:
                    # 其他价值字段（销售额、利润等）
                    column = field['column']
                    if column in interval_data.columns:
                        total_value = interval_data[column].sum()

                        # 计算盈利和亏损分布（仅对利润字段）
                        if field['key'] == 'profit':
                            profit_data = interval_data[column]
                            profit_sum = profit_data[profit_data > 0].sum()
                            loss_sum = abs(profit_data[profit_data < 0].sum())

                            value_item = {
                                'interval': interval_name,
                                'value': round(total_value, 2),
                                'profit_value': round(profit_sum, 2),
                                'loss_value': round(loss_sum, 2),
                                'percentage': round(total_value / data[column].sum() * 100, 2) if data[column].sum() != 0 else 0
                            }
                        else:
                            value_item = {
                                'interval': interval_name,
                                'value': round(total_value, 2),
                                'percentage': round(total_value / data[column].sum() * 100, 2) if data[column].sum() != 0 else 0
                            }
                    else:
                        value_item = {
                            'interval': interval_name,
                            'value': 0,
                            'percentage': 0
                        }

                value_distribution_data[field['key']].append(value_item)

            # 详细数据（用于下钻）
            items = []
            for _, row in interval_data.iterrows():
                item = {
                    'name': row[group_column],
                    'cost_rate': round(row['成本率'], 4),
                }

                # 添加所有可用的价值字段
                for field in value_fields:
                    if field['key'] != 'count' and 'column' in field:
                        column = field['column']
                        if column in row:
                            item[field['key']] = round(row[column], 2)

                # 添加其他有用字段
                if 'amount' in self.field_mapping:
                    item['amount'] = round(row[self.field_mapping['amount']], 2)
                if 'quantity' in self.field_mapping:
                    item['quantity'] = round(row[self.field_mapping['quantity']], 2)

                items.append(item)

            # 按成本率降序排序
            items.sort(key=lambda x: x['cost_rate'], reverse=True)
            interval_details[interval_name] = items

        return distribution_data, value_distribution_data, interval_details

    def _cost_efficiency_analysis(self, data: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """成本效率分析"""
        # 根据分析类型选择效率指标
        efficiency_field_map = {
            'product': 'quantity',  # 成本率 vs 销量
            'customer': 'amount',   # 成本率 vs 采购金额
            'region': 'amount'      # 成本率 vs 销售金额
        }

        efficiency_field = efficiency_field_map[analysis_type]

        if '成本率' not in data.columns or efficiency_field not in self.field_mapping:
            return {'error': '缺少成本效率分析所需字段'}

        efficiency_column = self.field_mapping[efficiency_field]

        # 计算平均值用于分类
        avg_cost_rate = data['成本率'].mean()
        avg_efficiency = data[efficiency_column].mean()

        # 准备散点图数据
        scatter_data = []
        for _, row in data.iterrows():
            if pd.notna(row['成本率']) and pd.notna(row[efficiency_column]):
                scatter_data.append({
                    'cost_rate': float(row['成本率']),
                    'efficiency_value': float(row[efficiency_column]),
                    'name': row[self._get_group_column(analysis_type)],
                    'quadrant': self._classify_cost_efficiency(row['成本率'], row[efficiency_column], avg_cost_rate, avg_efficiency)
                })

        return {
            'scatter_data': scatter_data,
            'x_label': '成本率',
            'y_label': self._get_efficiency_label(analysis_type),
            'avg_cost_rate': float(avg_cost_rate),
            'avg_efficiency': float(avg_efficiency)
        }

    def _classify_cost_efficiency(self, cost_rate: float, efficiency_value: float, avg_cost_rate: float, avg_efficiency: float) -> str:
        """成本效率象限分类"""
        if cost_rate < avg_cost_rate and efficiency_value > avg_efficiency:  # 低成本高效率
            return 'efficient'
        elif cost_rate < avg_cost_rate and efficiency_value <= avg_efficiency:  # 低成本低效率
            return 'low_volume'
        elif cost_rate >= avg_cost_rate and efficiency_value > avg_efficiency:  # 高成本高效率
            return 'high_cost'
        else:  # 高成本低效率
            return 'inefficient'

    def _get_efficiency_label(self, analysis_type: str) -> str:
        """获取效率指标标签"""
        labels = {
            'product': '销量(吨)',
            'customer': '采购金额(万元)',
            'region': '销售金额(万元)'
        }
        return labels.get(analysis_type, '效率指标')

    def _get_group_column(self, analysis_type: str) -> str:
        """获取分组列名"""
        group_field_map = {
            'product': 'product',
            'customer': 'customer',
            'region': 'region'
        }

        field_key = group_field_map.get(analysis_type)
        if field_key and field_key in self.field_mapping:
            return self.field_mapping[field_key]

        # 如果没有找到对应字段，返回第一个可用的字段
        for field_key in ['product', 'customer', 'region']:
            if field_key in self.field_mapping:
                return self.field_mapping[field_key]

        # 最后的备选方案
        return list(self.raw_data.columns)[0] if len(self.raw_data.columns) > 0 else 'unknown'
