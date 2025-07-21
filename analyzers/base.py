"""
分析器基类
Base Analyzer Class

提供所有分析器的通用功能和接口定义
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """分析器基类"""
    
    def __init__(self, data: pd.DataFrame, field_mapping: Dict[str, str] = None):
        """
        初始化基础分析器
        
        Args:
            data: 待分析的数据框
            field_mapping: 字段映射字典
        """
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.field_mapping = field_mapping or {}
        self.result = {}
        
    @abstractmethod
    def analyze(self, **kwargs) -> Dict[str, Any]:
        """
        执行分析（子类必须实现）
        
        Returns:
            Dict[str, Any]: 分析结果
        """
        pass
    
    def validate_data(self) -> bool:
        """
        验证数据有效性
        
        Returns:
            bool: 数据是否有效
        """
        if self.data.empty:
            logger.error("数据为空")
            return False
            
        # 检查必需字段
        missing_fields = self.get_missing_required_fields()
        if missing_fields:
            logger.error(f"缺少必需字段: {missing_fields}")
            return False
            
        return True
    
    def get_missing_required_fields(self) -> List[str]:
        """
        获取缺失的必需字段
        
        Returns:
            List[str]: 缺失字段列表
        """
        required_fields = self.get_required_fields()
        available_fields = set(self.data.columns)
        
        missing = []
        for field in required_fields:
            mapped_field = self.field_mapping.get(field, field)
            if mapped_field not in available_fields:
                missing.append(field)
                
        return missing
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        获取必需字段列表（子类必须实现）
        
        Returns:
            List[str]: 必需字段列表
        """
        pass
    
    def prepare_data(self) -> pd.DataFrame:
        """
        预处理数据
        
        Returns:
            pd.DataFrame: 处理后的数据
        """
        # 基础数据清理
        cleaned_data = self.data.copy()
        
        # 移除空行
        cleaned_data = cleaned_data.dropna(how='all')
        
        # 应用字段映射
        if self.field_mapping:
            rename_dict = {}
            for std_field, actual_field in self.field_mapping.items():
                if actual_field in cleaned_data.columns:
                    rename_dict[actual_field] = std_field
            cleaned_data = cleaned_data.rename(columns=rename_dict)
        
        return cleaned_data
    
    def get_field_value(self, field_name: str) -> str:
        """
        获取映射后的字段名
        
        Args:
            field_name: 标准字段名
            
        Returns:
            str: 实际字段名
        """
        return self.field_mapping.get(field_name, field_name)
    
    def format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化分析结果
        
        Args:
            result: 原始结果
            
        Returns:
            Dict[str, Any]: 格式化后的结果
        """
        # 基础格式化，子类可以重写
        return result
    
    def log_analysis_start(self, analysis_name: str):
        """记录分析开始"""
        logger.info(f"开始执行{analysis_name}分析")
        logger.info(f"数据规模: {len(self.data)}行 × {len(self.data.columns)}列")
    
    def log_analysis_complete(self, analysis_name: str):
        """记录分析完成"""
        logger.info(f"{analysis_name}分析完成")