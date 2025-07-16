#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析核心模块
Data Analysis Core Module

Author: Augment Agent
Date: 2025-07-15
"""

import pandas as pd
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
            
            # 计算成本率
            if 'amount' in self.field_mapping:
                amount_col = self.field_mapping['amount']
                result_data['成本率'] = (result_data['总成本'] / result_data[amount_col]).fillna(0)
        
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
            aggregated['成本率'] = (aggregated['总成本'] / aggregated[amount_col]).fillna(0)
        
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

        # 为每个数据点添加象限名称和策略
        data['象限名称'] = data['象限'].map(lambda q: quadrant_info[q]['name'])
        data['建议策略'] = data['象限'].map(lambda q: quadrant_info[q]['strategy'])

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

        return {
            'scatter_data': safe_to_dict(data),
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
        """分布区间分析"""
        # 根据分析类型定义区间
        interval_configs = {
            'product': {
                'field': 'quantity',
                'intervals': [0, 5, 10, 20, 50, float('inf')],
                'labels': ['<5吨', '5-10吨', '10-20吨', '20-50吨', '>50吨'],
                'title': '销量分布区间'
            },
            'customer': {
                'field': 'amount',
                'intervals': [0, 10, 50, 100, 500, float('inf')],
                'labels': ['<10万', '10-50万', '50-100万', '100-500万', '>500万'],
                'title': '采购金额分布区间'
            },
            'region': {
                'field': 'amount',
                'intervals': [0, 50, 200, 500, 1000, float('inf')],
                'labels': ['<50万', '50-200万', '200-500万', '500-1000万', '>1000万'],
                'title': '销售金额分布区间'
            }
        }

        config = interval_configs[analysis_type]
        if config['field'] not in self.field_mapping:
            raise ValueError(f"缺少分布分析所需字段: {config['field']}")
        field_column = self.field_mapping[config['field']]

        # 创建区间分组
        data['区间'] = pd.cut(data[field_column],
                           bins=config['intervals'],
                           labels=config['labels'],
                           right=False)

        # 统计各区间数据
        interval_stats = data.groupby('区间', observed=True).agg({
            field_column: ['count', 'sum', 'mean']
        }).round(2)

        interval_stats.columns = ['数量', '总值', '平均值']
        interval_stats['占比'] = (interval_stats['数量'] / len(data) * 100).round(2)

        return {
            'title': config['title'],
            'interval_data': safe_to_dict(interval_stats.reset_index()),
            'raw_data_with_intervals': safe_to_dict(data)
        }

    def _profit_loss_analysis(self, data: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """盈亏分析"""
        if 'profit' not in self.field_mapping:
            raise ValueError("缺少盈亏分析所需的毛利字段")
        profit_column = self.field_mapping['profit']

        # 分离盈利和亏损数据
        profitable = data[data[profit_column] > 0]
        loss_making = data[data[profit_column] <= 0]

        # 统计信息
        total_count = len(data)
        profitable_count = len(profitable)
        loss_count = len(loss_making)

        profitable_percentage = round(profitable_count / total_count * 100, 2) if total_count > 0 else 0
        loss_percentage = round(loss_count / total_count * 100, 2) if total_count > 0 else 0

        # 盈亏金额统计
        total_profit = profitable[profit_column].sum() if len(profitable) > 0 else 0
        total_loss = abs(loss_making[profit_column].sum()) if len(loss_making) > 0 else 0
        net_profit = total_profit - total_loss

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
            'profitable_items': safe_to_dict(profitable),
            'loss_making_items': safe_to_dict(loss_making)
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
        has_total_cost = '总成本(万元)' in data.columns
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
        """成本率分布分析"""
        cost_rates = data['成本率'].dropna()

        # 定义成本率区间
        intervals = [0, 0.3, 0.5, 0.7, 0.8, 1.0]
        labels = ['<30%', '30-50%', '50-70%', '70-80%', '>80%']

        # 创建区间分组
        cost_rate_intervals = pd.cut(cost_rates, bins=intervals, labels=labels, right=False)

        # 统计各区间数据
        interval_stats = cost_rate_intervals.value_counts().sort_index()

        distribution_data = []
        for interval, count in interval_stats.items():
            distribution_data.append({
                'interval': str(interval),
                'count': int(count),
                'percentage': round(count / len(cost_rates) * 100, 2)
            })

        return {
            'distribution_data': distribution_data,
            'avg_cost_rate': float(cost_rates.mean()),
            'median_cost_rate': float(cost_rates.median())
        }

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
