"""
分析器工厂
Analyzer Factory

提供创建各种分析器实例的工厂类
"""

from typing import Dict, Any, Type, List
import pandas as pd
from .base import BaseAnalyzer
from .quadrant_analyzer import QuadrantAnalyzer
from .pareto_analyzer import ParetoAnalyzer
from .distribution_analyzer import DistributionAnalyzer
import logging

logger = logging.getLogger(__name__)

class AnalyzerFactory:
    """分析器工厂类"""
    
    # 注册的分析器类型
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {
        'quadrant': QuadrantAnalyzer,
        'pareto': ParetoAnalyzer,
        'distribution': DistributionAnalyzer,
        'cost_rate_distribution': DistributionAnalyzer,
        'price_distribution': DistributionAnalyzer,
        'margin_distribution': DistributionAnalyzer
    }
    
    @classmethod
    def create_analyzer(cls, analyzer_type: str, data: pd.DataFrame,
                       field_mapping: Dict[str, str] = None) -> BaseAnalyzer:
        """
        创建分析器实例
        
        Args:
            analyzer_type: 分析器类型
            data: 待分析数据
            field_mapping: 字段映射
            
        Returns:
            BaseAnalyzer: 分析器实例
            
        Raises:
            ValueError: 如果分析器类型不支持
        """
        if analyzer_type not in cls._analyzers:
            raise ValueError(f"不支持的分析器类型: {analyzer_type}")
        
        analyzer_class = cls._analyzers[analyzer_type]
        logger.info(f"创建{analyzer_type}分析器")
        
        return analyzer_class(data, field_mapping)
    
    @classmethod
    def get_available_analyzers(cls) -> List[str]:
        """
        获取可用的分析器类型列表
        
        Returns:
            List[str]: 分析器类型列表
        """
        return list(cls._analyzers.keys())
    
    @classmethod
    def register_analyzer(cls, analyzer_type: str, analyzer_class: Type[BaseAnalyzer]):
        """
        注册新的分析器类型
        
        Args:
            analyzer_type: 分析器类型名称
            analyzer_class: 分析器类
        """
        if not issubclass(analyzer_class, BaseAnalyzer):
            raise ValueError(f"{analyzer_class}必须继承自BaseAnalyzer")
        
        cls._analyzers[analyzer_type] = analyzer_class
        logger.info(f"注册新分析器类型: {analyzer_type}")
    
    @classmethod
    def create_and_analyze(cls, analyzer_type: str, data: pd.DataFrame,
                         field_mapping: Dict[str, str] = None,
                         **analysis_params) -> Dict[str, Any]:
        """
        创建分析器并执行分析（便捷方法）
        
        Args:
            analyzer_type: 分析器类型
            data: 待分析数据
            field_mapping: 字段映射
            **analysis_params: 分析参数
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        analyzer = cls.create_analyzer(analyzer_type, data, field_mapping)
        
        # 根据分析器类型调用相应的分析方法
        if analyzer_type == 'quadrant':
            return analyzer.analyze(
                value_field=analysis_params.get('value_field', 'value'),
                quantity_field=analysis_params.get('quantity_field', 'quantity'),
                group_field=analysis_params.get('group_field', 'group')
            )
        elif analyzer_type == 'pareto':
            return analyzer.analyze(
                value_field=analysis_params.get('value_field', 'value'),
                group_field=analysis_params.get('group_field', 'group'),
                dimension_field=analysis_params.get('dimension_field'),
                pareto_threshold=analysis_params.get('pareto_threshold', 80.0)
            )
        elif analyzer_type in ['distribution', 'cost_rate_distribution', 
                              'price_distribution', 'margin_distribution']:
            # 根据具体类型设置分析参数
            if analyzer_type == 'cost_rate_distribution':
                return analyzer.analyze(
                    analysis_type='cost_rate',
                    cost_field=analysis_params.get('cost_field', 'cost'),
                    revenue_field=analysis_params.get('revenue_field', 'revenue'),
                    group_field=analysis_params.get('group_field'),
                    bins=analysis_params.get('bins', 10)
                )
            elif analyzer_type == 'price_distribution':
                return analyzer.analyze(
                    analysis_type='price',
                    price_field=analysis_params.get('price_field', 'price'),
                    quantity_field=analysis_params.get('quantity_field', 'quantity'),
                    bins=analysis_params.get('bins', 10)
                )
            elif analyzer_type == 'margin_distribution':
                return analyzer.analyze(
                    analysis_type='margin',
                    revenue_field=analysis_params.get('revenue_field', 'revenue'),
                    cost_field=analysis_params.get('cost_field', 'cost'),
                    bins=analysis_params.get('bins', 10)
                )
            else:
                return analyzer.analyze(**analysis_params)
        else:
            # 默认调用analyze方法
            return analyzer.analyze(**analysis_params)