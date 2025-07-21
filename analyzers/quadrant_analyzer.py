"""
四象限分析器
Quadrant Analyzer

实现基于价值和数量的四象限分析
"""

from .base import BaseAnalyzer
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class QuadrantAnalyzer(BaseAnalyzer):
    """四象限分析器"""
    
    def __init__(self, data: pd.DataFrame, field_mapping: Dict[str, str] = None):
        """
        初始化四象限分析器
        
        Args:
            data: 待分析的数据框
            field_mapping: 字段映射字典
        """
        super().__init__(data, field_mapping)
        self.value_field = None
        self.quantity_field = None
        self.group_field = None
        
    def get_required_fields(self) -> List[str]:
        """获取必需字段列表"""
        return ['value', 'quantity', 'group']
    
    def analyze(self, value_field: str, quantity_field: str, group_field: str, 
                value_threshold: float = None, quantity_threshold: float = None) -> Dict[str, Any]:
        """
        执行四象限分析
        
        Args:
            value_field: 价值字段名
            quantity_field: 数量字段名
            group_field: 分组字段名
            value_threshold: 价值阈值（可选，默认使用中位数）
            quantity_threshold: 数量阈值（可选，默认使用中位数）
            
        Returns:
            Dict[str, Any]: 四象限分析结果
        """
        self.log_analysis_start("四象限")
        
        # 设置字段
        self.value_field = self.get_field_value(value_field)
        self.quantity_field = self.get_field_value(quantity_field)
        self.group_field = self.get_field_value(group_field)
        
        # 验证数据
        if not self.validate_data():
            return {"error": "数据验证失败"}
        
        # 预处理数据
        prepared_data = self.prepare_data()
        
        # 聚合数据
        aggregated_data = self._aggregate_data(prepared_data)
        
        # 计算阈值
        if value_threshold is None:
            value_threshold = aggregated_data[self.value_field].median()
        if quantity_threshold is None:
            quantity_threshold = aggregated_data[self.quantity_field].median()
        
        # 分类四象限
        quadrant_data = self._classify_quadrants(
            aggregated_data, value_threshold, quantity_threshold
        )
        
        # 计算统计信息
        statistics = self._calculate_statistics(aggregated_data)
        
        # 计算各象限占比
        quadrant_summary = self._calculate_quadrant_summary(quadrant_data, aggregated_data)
        
        result = {
            'aggregated_data': aggregated_data.to_dict('records'),
            'quadrant_data': quadrant_data,
            'statistics': statistics,
            'quadrant_summary': quadrant_summary,
            'thresholds': {
                'value': value_threshold,
                'quantity': quantity_threshold
            }
        }
        
        self.log_analysis_complete("四象限")
        return self.format_result(result)
    
    def _aggregate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        聚合数据
        
        Args:
            data: 原始数据
            
        Returns:
            pd.DataFrame: 聚合后的数据
        """
        # 确保数值字段为数值类型
        data[self.value_field] = pd.to_numeric(data[self.value_field], errors='coerce')
        data[self.quantity_field] = pd.to_numeric(data[self.quantity_field], errors='coerce')
        
        # 移除包含空值的行
        data = data.dropna(subset=[self.value_field, self.quantity_field, self.group_field])
        
        # 按分组字段聚合
        aggregated = data.groupby(self.group_field).agg({
            self.value_field: 'sum',
            self.quantity_field: 'sum'
        }).reset_index()
        
        # 计算占比
        total_value = aggregated[self.value_field].sum()
        total_quantity = aggregated[self.quantity_field].sum()
        
        aggregated['value_ratio'] = aggregated[self.value_field] / total_value * 100
        aggregated['quantity_ratio'] = aggregated[self.quantity_field] / total_quantity * 100
        
        # 计算累计占比（用于帕累托分析）
        aggregated = aggregated.sort_values(self.value_field, ascending=False)
        aggregated['value_cumsum'] = aggregated['value_ratio'].cumsum()
        aggregated['quantity_cumsum'] = aggregated['quantity_ratio'].cumsum()
        
        return aggregated
    
    def _classify_quadrants(self, data: pd.DataFrame, value_threshold: float, 
                          quantity_threshold: float) -> Dict[str, List[Dict]]:
        """
        分类四象限
        
        Args:
            data: 聚合后的数据
            value_threshold: 价值阈值
            quantity_threshold: 数量阈值
            
        Returns:
            Dict[str, List[Dict]]: 四象限分类结果
        """
        quadrants = {
            'star': [],       # 明星产品：高价值，高数量
            'cash_cow': [],   # 现金牛：高价值，低数量
            'question': [],   # 问题产品：低价值，高数量
            'dog': []        # 瘦狗产品：低价值，低数量
        }
        
        for _, row in data.iterrows():
            item_info = {
                'name': row[self.group_field],
                'value': row[self.value_field],
                'quantity': row[self.quantity_field],
                'value_ratio': row['value_ratio'],
                'quantity_ratio': row['quantity_ratio']
            }
            
            if row[self.value_field] >= value_threshold:
                if row[self.quantity_field] >= quantity_threshold:
                    quadrants['star'].append(item_info)
                else:
                    quadrants['cash_cow'].append(item_info)
            else:
                if row[self.quantity_field] >= quantity_threshold:
                    quadrants['question'].append(item_info)
                else:
                    quadrants['dog'].append(item_info)
        
        # 对每个象限内的数据按价值排序
        for quadrant in quadrants:
            quadrants[quadrant].sort(key=lambda x: x['value'], reverse=True)
        
        return quadrants
    
    def _calculate_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        计算统计信息
        
        Args:
            data: 聚合后的数据
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_value': float(data[self.value_field].sum()),
            'total_quantity': float(data[self.quantity_field].sum()),
            'value_mean': float(data[self.value_field].mean()),
            'value_median': float(data[self.value_field].median()),
            'value_std': float(data[self.value_field].std()),
            'quantity_mean': float(data[self.quantity_field].mean()),
            'quantity_median': float(data[self.quantity_field].median()),
            'quantity_std': float(data[self.quantity_field].std()),
            'item_count': len(data)
        }
    
    def _calculate_quadrant_summary(self, quadrant_data: Dict[str, List[Dict]], 
                                  aggregated_data: pd.DataFrame) -> Dict[str, Dict]:
        """
        计算各象限汇总信息
        
        Args:
            quadrant_data: 四象限分类结果
            aggregated_data: 聚合数据
            
        Returns:
            Dict[str, Dict]: 各象限汇总信息
        """
        total_value = aggregated_data[self.value_field].sum()
        total_quantity = aggregated_data[self.quantity_field].sum()
        total_items = len(aggregated_data)
        
        summary = {}
        
        quadrant_names = {
            'star': '明星产品',
            'cash_cow': '现金牛产品',
            'question': '问题产品',
            'dog': '瘦狗产品'
        }
        
        for quadrant_key, items in quadrant_data.items():
            quadrant_value = sum(item['value'] for item in items)
            quadrant_quantity = sum(item['quantity'] for item in items)
            
            summary[quadrant_key] = {
                'name': quadrant_names[quadrant_key],
                'item_count': len(items),
                'item_ratio': len(items) / total_items * 100 if total_items > 0 else 0,
                'total_value': quadrant_value,
                'value_ratio': quadrant_value / total_value * 100 if total_value > 0 else 0,
                'total_quantity': quadrant_quantity,
                'quantity_ratio': quadrant_quantity / total_quantity * 100 if total_quantity > 0 else 0
            }
        
        return summary