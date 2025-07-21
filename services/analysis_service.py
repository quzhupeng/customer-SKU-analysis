"""
分析服务
Analysis Service

提供高级分析功能和业务逻辑
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from analyzers.factory import AnalyzerFactory
from .data_service import DataService
from utils.exceptions import InvalidAnalysisTypeError, AnalysisError
import logging
import time

logger = logging.getLogger(__name__)

class AnalysisService:
    """分析服务类"""
    
    def __init__(self, data_service: DataService):
        """
        初始化分析服务
        
        Args:
            data_service: 数据服务实例
        """
        self.data_service = data_service
        self._analysis_history = []  # 分析历史记录
    
    def perform_analysis(self, file_id: str, sheet_name: str, 
                        analysis_type: str, field_mapping: Dict[str, str],
                        analysis_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行分析
        
        Args:
            file_id: 文件ID
            sheet_name: 工作表名称
            analysis_type: 分析类型
            field_mapping: 字段映射
            analysis_params: 分析参数
            
        Returns:
            Dict[str, Any]: 分析结果
            
        Raises:
            InvalidAnalysisTypeError: 无效的分析类型
            AnalysisError: 分析失败
        """
        start_time = time.time()
        
        # 验证分析类型
        available_types = AnalyzerFactory.get_available_analyzers()
        if analysis_type not in available_types:
            raise InvalidAnalysisTypeError(
                f"不支持的分析类型: {analysis_type}",
                {'available_types': available_types}
            )
        
        try:
            # 加载数据
            logger.info(f"开始执行{analysis_type}分析 - 文件: {file_id}, 工作表: {sheet_name}")
            sheet_data = self.data_service.get_sheet_data(file_id, sheet_name)
            
            # 创建分析器
            analyzer = AnalyzerFactory.create_analyzer(
                analysis_type, sheet_data, field_mapping
            )
            
            # 执行分析
            analysis_params = analysis_params or {}
            result = self._execute_analysis(analyzer, analysis_type, analysis_params)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 添加元数据
            analysis_result = {
                'analysis_type': analysis_type,
                'file_id': file_id,
                'sheet_name': sheet_name,
                'execution_time': execution_time,
                'data_rows': len(sheet_data),
                'result': result
            }
            
            # 记录历史
            self._record_analysis_history(analysis_result)
            
            logger.info(f"{analysis_type}分析完成，耗时: {execution_time:.2f}秒")
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析失败: {str(e)}")
            raise AnalysisError(f"分析失败: {str(e)}", {
                'analysis_type': analysis_type,
                'file_id': file_id,
                'sheet_name': sheet_name
            })
    
    def get_field_suggestions(self, file_id: str, sheet_name: str, 
                            analysis_type: str) -> Dict[str, Any]:
        """
        获取字段建议
        
        Args:
            file_id: 文件ID
            sheet_name: 工作表名称
            analysis_type: 分析类型
            
        Returns:
            Dict[str, Any]: 字段建议
        """
        # 获取数据
        sheet_data = self.data_service.get_sheet_data(file_id, sheet_name)
        
        # 检测列类型
        column_types = self.data_service.detect_columns(sheet_data)
        
        # 根据分析类型生成建议
        suggestions = self._generate_field_suggestions(
            column_types, analysis_type, sheet_data
        )
        
        return {
            'column_types': column_types,
            'suggestions': suggestions
        }
    
    def validate_analysis_params(self, analysis_type: str, 
                               params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证分析参数
        
        Args:
            analysis_type: 分析类型
            params: 分析参数
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误消息列表)
        """
        errors = []
        
        # 根据分析类型验证参数
        if analysis_type == 'quadrant':
            required = ['value_field', 'quantity_field', 'group_field']
            for field in required:
                if field not in params:
                    errors.append(f"缺少必需参数: {field}")
        
        elif analysis_type == 'pareto':
            required = ['value_field', 'group_field']
            for field in required:
                if field not in params:
                    errors.append(f"缺少必需参数: {field}")
        
        elif analysis_type in ['cost_rate_distribution', 'margin_distribution']:
            required = ['cost_field', 'revenue_field']
            for field in required:
                if field not in params:
                    errors.append(f"缺少必需参数: {field}")
        
        elif analysis_type == 'price_distribution':
            required = ['price_field', 'quantity_field']
            for field in required:
                if field not in params:
                    errors.append(f"缺少必需参数: {field}")
        
        return len(errors) == 0, errors
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取分析历史
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 分析历史记录
        """
        # 返回最近的记录
        return self._analysis_history[-limit:][::-1]
    
    def _execute_analysis(self, analyzer, analysis_type: str, 
                        params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行具体的分析
        
        Args:
            analyzer: 分析器实例
            analysis_type: 分析类型
            params: 分析参数
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 根据分析类型调用相应的方法
        if analysis_type == 'quadrant':
            return analyzer.analyze(
                value_field=params['value_field'],
                quantity_field=params['quantity_field'],
                group_field=params['group_field'],
                value_threshold=params.get('value_threshold'),
                quantity_threshold=params.get('quantity_threshold')
            )
        
        elif analysis_type == 'pareto':
            return analyzer.analyze(
                value_field=params['value_field'],
                group_field=params['group_field'],
                dimension_field=params.get('dimension_field'),
                pareto_threshold=params.get('pareto_threshold', 80.0)
            )
        
        elif analysis_type == 'cost_rate_distribution':
            return analyzer.analyze(
                analysis_type='cost_rate',
                cost_field=params['cost_field'],
                revenue_field=params['revenue_field'],
                group_field=params.get('group_field'),
                bins=params.get('bins', 10)
            )
        
        elif analysis_type == 'price_distribution':
            return analyzer.analyze(
                analysis_type='price',
                price_field=params['price_field'],
                quantity_field=params['quantity_field'],
                bins=params.get('bins', 10)
            )
        
        elif analysis_type == 'margin_distribution':
            return analyzer.analyze(
                analysis_type='margin',
                revenue_field=params['revenue_field'],
                cost_field=params['cost_field'],
                bins=params.get('bins', 10)
            )
        
        else:
            # 默认调用
            return analyzer.analyze(**params)
    
    def _generate_field_suggestions(self, column_types: Dict[str, List[str]], 
                                  analysis_type: str, 
                                  data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成字段建议
        
        Args:
            column_types: 列类型分类
            analysis_type: 分析类型
            data: 数据框
            
        Returns:
            Dict[str, Any]: 字段建议
        """
        suggestions = {}
        numeric_cols = column_types['numeric']
        text_cols = column_types['text']
        
        if analysis_type == 'quadrant':
            # 四象限分析建议
            suggestions['value_field'] = self._suggest_value_field(numeric_cols, data)
            suggestions['quantity_field'] = self._suggest_quantity_field(numeric_cols, data)
            suggestions['group_field'] = self._suggest_group_field(text_cols, data)
        
        elif analysis_type == 'pareto':
            # 帕累托分析建议
            suggestions['value_field'] = self._suggest_value_field(numeric_cols, data)
            suggestions['group_field'] = self._suggest_group_field(text_cols, data)
            suggestions['dimension_field'] = self._suggest_dimension_field(text_cols, data)
        
        elif analysis_type in ['cost_rate_distribution', 'margin_distribution']:
            # 成本率/利润率分析建议
            suggestions['cost_field'] = self._suggest_cost_field(numeric_cols, data)
            suggestions['revenue_field'] = self._suggest_revenue_field(numeric_cols, data)
            if analysis_type == 'cost_rate_distribution':
                suggestions['group_field'] = self._suggest_group_field(text_cols, data)
        
        elif analysis_type == 'price_distribution':
            # 价格分布分析建议
            suggestions['price_field'] = self._suggest_price_field(numeric_cols, data)
            suggestions['quantity_field'] = self._suggest_quantity_field(numeric_cols, data)
        
        return suggestions
    
    def _suggest_value_field(self, numeric_cols: List[str], data: pd.DataFrame) -> Optional[str]:
        """建议价值字段"""
        # 查找包含"金额"、"销售"、"价值"等关键词的列
        keywords = ['金额', '销售', '营业', '收入', '价值', 'amount', 'sales', 'revenue', 'value']
        for col in numeric_cols:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        # 如果没有找到，返回数值最大的列
        if numeric_cols:
            max_col = max(numeric_cols, key=lambda x: data[x].sum())
            return max_col
        return None
    
    def _suggest_quantity_field(self, numeric_cols: List[str], data: pd.DataFrame) -> Optional[str]:
        """建议数量字段"""
        # 查找包含"数量"、"销量"等关键词的列
        keywords = ['数量', '销量', '件数', 'quantity', 'qty', 'count', 'volume']
        for col in numeric_cols:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        return numeric_cols[0] if numeric_cols else None
    
    def _suggest_group_field(self, text_cols: List[str], data: pd.DataFrame) -> Optional[str]:
        """建议分组字段"""
        # 查找包含产品、商品、名称等关键词的列
        keywords = ['产品', '商品', '物料', '名称', 'product', 'item', 'name', 'sku']
        for col in text_cols:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        # 返回唯一值数量适中的列
        if text_cols:
            suitable_cols = [
                col for col in text_cols 
                if 5 <= data[col].nunique() <= 100
            ]
            if suitable_cols:
                return suitable_cols[0]
        return text_cols[0] if text_cols else None
    
    def _suggest_cost_field(self, numeric_cols: List[str], data: pd.DataFrame) -> Optional[str]:
        """建议成本字段"""
        keywords = ['成本', '费用', 'cost', 'expense']
        for col in numeric_cols:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        return None
    
    def _suggest_revenue_field(self, numeric_cols: List[str], data: pd.DataFrame) -> Optional[str]:
        """建议收入字段"""
        keywords = ['收入', '销售', '营业', '金额', 'revenue', 'sales', 'income']
        for col in numeric_cols:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        return None
    
    def _suggest_price_field(self, numeric_cols: List[str], data: pd.DataFrame) -> Optional[str]:
        """建议价格字段"""
        keywords = ['价格', '单价', 'price', 'unit_price']
        for col in numeric_cols:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        return None
    
    def _suggest_dimension_field(self, text_cols: List[str], data: pd.DataFrame) -> Optional[str]:
        """建议维度字段"""
        # 查找分类、类别等字段
        keywords = ['类别', '分类', '类型', '品类', 'category', 'type', 'class']
        for col in text_cols:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        # 返回唯一值较少的列（2-20个）
        if text_cols:
            suitable_cols = [
                col for col in text_cols 
                if 2 <= data[col].nunique() <= 20
            ]
            if suitable_cols:
                return suitable_cols[0]
        return None
    
    def _record_analysis_history(self, analysis_result: Dict[str, Any]):
        """记录分析历史"""
        # 只保留必要信息，避免存储大量数据
        history_entry = {
            'timestamp': time.time(),
            'analysis_type': analysis_result['analysis_type'],
            'file_id': analysis_result['file_id'],
            'sheet_name': analysis_result['sheet_name'],
            'execution_time': analysis_result['execution_time'],
            'data_rows': analysis_result['data_rows']
        }
        
        self._analysis_history.append(history_entry)
        
        # 限制历史记录数量
        if len(self._analysis_history) > 100:
            self._analysis_history = self._analysis_history[-100:]