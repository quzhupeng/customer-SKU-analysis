"""
帕累托分析器
Pareto Analyzer

实现帕累托法则（80/20法则）分析
"""

from .base import BaseAnalyzer
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ParetoAnalyzer(BaseAnalyzer):
    """帕累托分析器"""
    
    def get_required_fields(self) -> List[str]:
        """获取必需字段列表"""
        return ['value', 'group']
    
    def analyze(self, value_field: str, group_field: str, 
                dimension_field: Optional[str] = None,
                pareto_threshold: float = 80.0) -> Dict[str, Any]:
        """
        执行帕累托分析
        
        Args:
            value_field: 价值字段名
            group_field: 分组字段名
            dimension_field: 维度字段名（可选，用于多维度分析）
            pareto_threshold: 帕累托阈值（默认80%）
            
        Returns:
            Dict[str, Any]: 帕累托分析结果
        """
        self.log_analysis_start("帕累托")
        
        # 获取映射后的字段名
        value_field = self.get_field_value(value_field)
        group_field = self.get_field_value(group_field)
        dimension_field = self.get_field_value(dimension_field) if dimension_field else None
        
        # 验证数据
        if not self.validate_data():
            return {"error": "数据验证失败"}
        
        # 预处理数据
        prepared_data = self.prepare_data()
        
        # 执行分析
        if dimension_field:
            result = self._analyze_multi_dimension(
                prepared_data, value_field, group_field, dimension_field, pareto_threshold
            )
        else:
            result = self._analyze_single_dimension(
                prepared_data, value_field, group_field, pareto_threshold
            )
        
        self.log_analysis_complete("帕累托")
        return self.format_result(result)
    
    def _analyze_single_dimension(self, data: pd.DataFrame, value_field: str, 
                                group_field: str, threshold: float) -> Dict[str, Any]:
        """
        单维度帕累托分析
        
        Args:
            data: 数据
            value_field: 价值字段
            group_field: 分组字段
            threshold: 阈值
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 确保数值字段为数值类型
        data[value_field] = pd.to_numeric(data[value_field], errors='coerce')
        
        # 移除空值
        data = data.dropna(subset=[value_field, group_field])
        
        # 聚合数据
        aggregated = data.groupby(group_field)[value_field].sum().reset_index()
        aggregated = aggregated.sort_values(value_field, ascending=False)
        
        # 计算累计百分比
        total_value = aggregated[value_field].sum()
        aggregated['value_ratio'] = aggregated[value_field] / total_value * 100
        aggregated['cumulative_ratio'] = aggregated['value_ratio'].cumsum()
        aggregated['item_cumulative_ratio'] = (np.arange(len(aggregated)) + 1) / len(aggregated) * 100
        
        # 找出帕累托分界点
        pareto_items = aggregated[aggregated['cumulative_ratio'] <= threshold]
        if len(pareto_items) == 0:
            # 如果没有项目达到阈值，至少包含第一个
            pareto_items = aggregated.head(1)
        
        # 计算ABC分类
        abc_classification = self._classify_abc(aggregated, 'cumulative_ratio')
        
        return {
            'data': aggregated.to_dict('records'),
            'pareto_summary': {
                'threshold': threshold,
                'pareto_items_count': len(pareto_items),
                'total_items_count': len(aggregated),
                'pareto_items_ratio': len(pareto_items) / len(aggregated) * 100,
                'pareto_value_ratio': pareto_items['value_ratio'].sum()
            },
            'abc_classification': abc_classification,
            'statistics': {
                'total_value': float(total_value),
                'average_value': float(aggregated[value_field].mean()),
                'median_value': float(aggregated[value_field].median()),
                'std_value': float(aggregated[value_field].std())
            }
        }
    
    def _analyze_multi_dimension(self, data: pd.DataFrame, value_field: str,
                               group_field: str, dimension_field: str,
                               threshold: float) -> Dict[str, Any]:
        """
        多维度帕累托分析
        
        Args:
            data: 数据
            value_field: 价值字段
            group_field: 分组字段
            dimension_field: 维度字段
            threshold: 阈值
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        dimensions = data[dimension_field].unique()
        dimension_results = {}
        
        for dimension in dimensions:
            dimension_data = data[data[dimension_field] == dimension]
            if len(dimension_data) > 0:
                dimension_results[str(dimension)] = self._analyze_single_dimension(
                    dimension_data, value_field, group_field, threshold
                )
        
        # 计算整体统计
        overall_stats = self._calculate_overall_stats(data, value_field, dimension_field)
        
        return {
            'dimension_results': dimension_results,
            'overall_statistics': overall_stats,
            'dimensions': list(dimension_results.keys())
        }
    
    def _classify_abc(self, data: pd.DataFrame, cumulative_field: str) -> Dict[str, List[Dict]]:
        """
        ABC分类
        
        Args:
            data: 排序后的数据
            cumulative_field: 累计百分比字段
            
        Returns:
            Dict[str, List[Dict]]: ABC分类结果
        """
        abc_classification = {
            'A': [],  # 累计占比0-80%
            'B': [],  # 累计占比80-95%
            'C': []   # 累计占比95-100%
        }
        
        for _, row in data.iterrows():
            item_dict = row.to_dict()
            cumulative_ratio = row[cumulative_field]
            
            if cumulative_ratio <= 80:
                abc_classification['A'].append(item_dict)
            elif cumulative_ratio <= 95:
                abc_classification['B'].append(item_dict)
            else:
                abc_classification['C'].append(item_dict)
        
        return abc_classification
    
    def _calculate_overall_stats(self, data: pd.DataFrame, value_field: str,
                               dimension_field: str) -> Dict[str, Any]:
        """
        计算整体统计信息
        
        Args:
            data: 数据
            value_field: 价值字段
            dimension_field: 维度字段
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        dimension_stats = data.groupby(dimension_field)[value_field].agg([
            'sum', 'mean', 'count'
        ]).reset_index()
        
        total_value = data[value_field].sum()
        dimension_stats['value_ratio'] = dimension_stats['sum'] / total_value * 100
        
        return {
            'dimension_comparison': dimension_stats.to_dict('records'),
            'total_value': float(total_value),
            'dimension_count': len(dimension_stats)
        }