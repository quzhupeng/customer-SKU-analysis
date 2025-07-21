"""
分布分析器
Distribution Analyzer

实现数据分布分析，包括成本率分布、价格分布等
"""

from .base import BaseAnalyzer
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DistributionAnalyzer(BaseAnalyzer):
    """分布分析器"""
    
    def get_required_fields(self) -> List[str]:
        """获取必需字段列表"""
        # 分布分析的必需字段根据具体分析类型而定
        return []
    
    def analyze(self, analysis_type: str = 'cost_rate', **kwargs) -> Dict[str, Any]:
        """
        执行分布分析
        
        Args:
            analysis_type: 分析类型 ('cost_rate', 'price', 'margin', 'custom')
            **kwargs: 其他参数，根据分析类型而定
            
        Returns:
            Dict[str, Any]: 分布分析结果
        """
        self.log_analysis_start(f"{analysis_type}分布")
        
        # 验证数据
        if not self.validate_data():
            return {"error": "数据验证失败"}
        
        # 预处理数据
        prepared_data = self.prepare_data()
        
        # 根据分析类型执行相应的分析
        if analysis_type == 'cost_rate':
            result = self._analyze_cost_rate_distribution(prepared_data, **kwargs)
        elif analysis_type == 'price':
            result = self._analyze_price_distribution(prepared_data, **kwargs)
        elif analysis_type == 'margin':
            result = self._analyze_margin_distribution(prepared_data, **kwargs)
        elif analysis_type == 'custom':
            result = self._analyze_custom_distribution(prepared_data, **kwargs)
        else:
            result = {"error": f"不支持的分析类型: {analysis_type}"}
        
        self.log_analysis_complete(f"{analysis_type}分布")
        return self.format_result(result)
    
    def _analyze_cost_rate_distribution(self, data: pd.DataFrame, 
                                      cost_field: str, revenue_field: str,
                                      group_field: Optional[str] = None,
                                      bins: int = 10) -> Dict[str, Any]:
        """
        成本率分布分析
        
        Args:
            data: 数据
            cost_field: 成本字段
            revenue_field: 收入字段
            group_field: 分组字段（可选）
            bins: 分组数量
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 获取映射后的字段名
        cost_field = self.get_field_value(cost_field)
        revenue_field = self.get_field_value(revenue_field)
        group_field = self.get_field_value(group_field) if group_field else None
        
        # 确保数值类型
        data[cost_field] = pd.to_numeric(data[cost_field], errors='coerce')
        data[revenue_field] = pd.to_numeric(data[revenue_field], errors='coerce')
        
        # 计算成本率
        data['cost_rate'] = data[cost_field] / data[revenue_field] * 100
        
        # 移除异常值
        data = data[(data['cost_rate'] >= 0) & (data['cost_rate'] <= 100)]
        
        # 创建分布区间
        distribution_data = self._create_distribution(data, 'cost_rate', bins)
        
        # 如果有分组字段，进行分组分析
        group_distributions = {}
        if group_field:
            groups = data[group_field].unique()
            for group in groups:
                group_data = data[data[group_field] == group]
                if len(group_data) > 0:
                    group_distributions[str(group)] = self._create_distribution(
                        group_data, 'cost_rate', bins
                    )
        
        # 计算统计信息
        statistics = {
            'mean': float(data['cost_rate'].mean()),
            'median': float(data['cost_rate'].median()),
            'std': float(data['cost_rate'].std()),
            'min': float(data['cost_rate'].min()),
            'max': float(data['cost_rate'].max()),
            'q1': float(data['cost_rate'].quantile(0.25)),
            'q3': float(data['cost_rate'].quantile(0.75))
        }
        
        result = {
            'distribution': distribution_data,
            'statistics': statistics,
            'total_items': len(data)
        }
        
        if group_distributions:
            result['group_distributions'] = group_distributions
        
        return result
    
    def _analyze_price_distribution(self, data: pd.DataFrame,
                                  price_field: str, quantity_field: str,
                                  bins: int = 10) -> Dict[str, Any]:
        """
        价格分布分析
        
        Args:
            data: 数据
            price_field: 价格字段
            quantity_field: 数量字段
            bins: 分组数量
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 获取映射后的字段名
        price_field = self.get_field_value(price_field)
        quantity_field = self.get_field_value(quantity_field)
        
        # 确保数值类型
        data[price_field] = pd.to_numeric(data[price_field], errors='coerce')
        data[quantity_field] = pd.to_numeric(data[quantity_field], errors='coerce')
        
        # 移除异常值
        data = data[data[price_field] > 0]
        
        # 创建价格分布
        distribution_data = self._create_weighted_distribution(
            data, price_field, quantity_field, bins
        )
        
        # 计算统计信息
        weighted_mean = (data[price_field] * data[quantity_field]).sum() / data[quantity_field].sum()
        
        statistics = {
            'mean': float(data[price_field].mean()),
            'weighted_mean': float(weighted_mean),
            'median': float(data[price_field].median()),
            'std': float(data[price_field].std()),
            'min': float(data[price_field].min()),
            'max': float(data[price_field].max())
        }
        
        return {
            'distribution': distribution_data,
            'statistics': statistics,
            'total_items': len(data),
            'total_quantity': float(data[quantity_field].sum())
        }
    
    def _analyze_margin_distribution(self, data: pd.DataFrame,
                                   revenue_field: str, cost_field: str,
                                   bins: int = 10) -> Dict[str, Any]:
        """
        利润率分布分析
        
        Args:
            data: 数据
            revenue_field: 收入字段
            cost_field: 成本字段
            bins: 分组数量
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 获取映射后的字段名
        revenue_field = self.get_field_value(revenue_field)
        cost_field = self.get_field_value(cost_field)
        
        # 确保数值类型
        data[revenue_field] = pd.to_numeric(data[revenue_field], errors='coerce')
        data[cost_field] = pd.to_numeric(data[cost_field], errors='coerce')
        
        # 计算利润率
        data['margin'] = (data[revenue_field] - data[cost_field]) / data[revenue_field] * 100
        
        # 移除异常值
        data = data[(data['margin'] >= -100) & (data['margin'] <= 100)]
        
        # 创建分布
        distribution_data = self._create_distribution(data, 'margin', bins)
        
        # 分类利润率水平
        margin_levels = {
            'high': data[data['margin'] >= 30],
            'medium': data[(data['margin'] >= 10) & (data['margin'] < 30)],
            'low': data[(data['margin'] >= 0) & (data['margin'] < 10)],
            'negative': data[data['margin'] < 0]
        }
        
        level_summary = {}
        for level, level_data in margin_levels.items():
            level_summary[level] = {
                'count': len(level_data),
                'ratio': len(level_data) / len(data) * 100,
                'avg_margin': float(level_data['margin'].mean()) if len(level_data) > 0 else 0
            }
        
        # 计算统计信息
        statistics = {
            'mean': float(data['margin'].mean()),
            'median': float(data['margin'].median()),
            'std': float(data['margin'].std()),
            'min': float(data['margin'].min()),
            'max': float(data['margin'].max())
        }
        
        return {
            'distribution': distribution_data,
            'statistics': statistics,
            'margin_levels': level_summary,
            'total_items': len(data)
        }
    
    def _analyze_custom_distribution(self, data: pd.DataFrame,
                                   value_field: str, bins: int = 10,
                                   weight_field: Optional[str] = None) -> Dict[str, Any]:
        """
        自定义分布分析
        
        Args:
            data: 数据
            value_field: 值字段
            bins: 分组数量
            weight_field: 权重字段（可选）
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 获取映射后的字段名
        value_field = self.get_field_value(value_field)
        weight_field = self.get_field_value(weight_field) if weight_field else None
        
        # 确保数值类型
        data[value_field] = pd.to_numeric(data[value_field], errors='coerce')
        
        # 创建分布
        if weight_field:
            data[weight_field] = pd.to_numeric(data[weight_field], errors='coerce')
            distribution_data = self._create_weighted_distribution(
                data, value_field, weight_field, bins
            )
        else:
            distribution_data = self._create_distribution(data, value_field, bins)
        
        # 计算统计信息
        statistics = {
            'mean': float(data[value_field].mean()),
            'median': float(data[value_field].median()),
            'std': float(data[value_field].std()),
            'min': float(data[value_field].min()),
            'max': float(data[value_field].max())
        }
        
        return {
            'distribution': distribution_data,
            'statistics': statistics,
            'total_items': len(data)
        }
    
    def _create_distribution(self, data: pd.DataFrame, value_field: str,
                           bins: int) -> List[Dict[str, Any]]:
        """
        创建分布数据
        
        Args:
            data: 数据
            value_field: 值字段
            bins: 分组数量
            
        Returns:
            List[Dict[str, Any]]: 分布数据
        """
        # 创建区间
        data['bin'] = pd.cut(data[value_field], bins=bins)
        
        # 统计每个区间
        distribution = []
        for interval in data['bin'].cat.categories:
            interval_data = data[data['bin'] == interval]
            
            distribution.append({
                'range': f"{interval.left:.2f} - {interval.right:.2f}",
                'min': float(interval.left),
                'max': float(interval.right),
                'count': len(interval_data),
                'ratio': len(interval_data) / len(data) * 100,
                'cumulative_ratio': 0  # 将在后面计算
            })
        
        # 计算累计百分比
        cumulative = 0
        for item in distribution:
            cumulative += item['ratio']
            item['cumulative_ratio'] = cumulative
        
        return distribution
    
    def _create_weighted_distribution(self, data: pd.DataFrame, value_field: str,
                                    weight_field: str, bins: int) -> List[Dict[str, Any]]:
        """
        创建加权分布数据
        
        Args:
            data: 数据
            value_field: 值字段
            weight_field: 权重字段
            bins: 分组数量
            
        Returns:
            List[Dict[str, Any]]: 分布数据
        """
        # 创建区间
        data['bin'] = pd.cut(data[value_field], bins=bins)
        
        total_weight = data[weight_field].sum()
        
        # 统计每个区间
        distribution = []
        for interval in data['bin'].cat.categories:
            interval_data = data[data['bin'] == interval]
            interval_weight = interval_data[weight_field].sum()
            
            distribution.append({
                'range': f"{interval.left:.2f} - {interval.right:.2f}",
                'min': float(interval.left),
                'max': float(interval.right),
                'count': len(interval_data),
                'ratio': len(interval_data) / len(data) * 100,
                'weight': float(interval_weight),
                'weight_ratio': interval_weight / total_weight * 100 if total_weight > 0 else 0,
                'cumulative_ratio': 0  # 将在后面计算
            })
        
        # 计算累计百分比
        cumulative = 0
        for item in distribution:
            cumulative += item['weight_ratio']
            item['cumulative_ratio'] = cumulative
        
        return distribution