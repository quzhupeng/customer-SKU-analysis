"""
数据服务
Data Service

处理数据加载、缓存和基本操作
"""

import pandas as pd
import os
from typing import Dict, List, Any, Optional, Tuple
from utils.exceptions import FileProcessingError, DataValidationError, DataLoadError
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class DataService:
    """数据服务类"""
    
    def __init__(self, upload_folder: str = 'uploads'):
        """
        初始化数据服务
        
        Args:
            upload_folder: 上传文件夹路径
        """
        self.upload_folder = upload_folder
        self._cache = {}  # 简单的内存缓存
        self._file_info_cache = {}  # 文件信息缓存
    
    def load_excel_file(self, file_path: str, use_cache: bool = True) -> Dict[str, pd.DataFrame]:
        """
        加载Excel文件
        
        Args:
            file_path: 文件路径（相对于upload_folder）
            use_cache: 是否使用缓存
            
        Returns:
            Dict[str, pd.DataFrame]: 工作表名称到数据框的映射
            
        Raises:
            FileProcessingError: 文件处理失败
            DataLoadError: 数据加载失败
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(file_path)
        
        # 如果启用缓存且缓存中存在数据
        if use_cache and cache_key in self._cache:
            logger.info(f"从缓存加载文件: {file_path}")
            return self._cache[cache_key]
        
        # 构建完整路径
        full_path = os.path.join(self.upload_folder, file_path)
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            raise FileProcessingError(f"文件不存在: {file_path}")
        
        try:
            # 读取所有工作表
            logger.info(f"正在加载Excel文件: {file_path}")
            excel_data = pd.read_excel(full_path, sheet_name=None)
            
            # 验证数据
            self._validate_excel_data(excel_data)
            
            # 清理数据
            cleaned_data = self._clean_excel_data(excel_data)
            
            # 缓存数据
            if use_cache:
                self._cache[cache_key] = cleaned_data
            
            # 缓存文件信息
            self._cache_file_info(file_path, cleaned_data)
            
            logger.info(f"成功加载Excel文件: {file_path}, 包含{len(cleaned_data)}个工作表")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"加载Excel文件失败: {str(e)}")
            raise DataLoadError(f"加载文件失败: {str(e)}", {'file_path': file_path})
    
    def get_sheet_data(self, file_path: str, sheet_name: str) -> pd.DataFrame:
        """
        获取指定工作表数据
        
        Args:
            file_path: 文件路径
            sheet_name: 工作表名称
            
        Returns:
            pd.DataFrame: 工作表数据
            
        Raises:
            DataValidationError: 工作表不存在
        """
        excel_data = self.load_excel_file(file_path)
        
        if sheet_name not in excel_data:
            available_sheets = list(excel_data.keys())
            raise DataValidationError(
                f"工作表'{sheet_name}'不存在",
                {'available_sheets': available_sheets}
            )
        
        return excel_data[sheet_name]
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        获取文件中的工作表名称列表
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 工作表名称列表
        """
        excel_data = self.load_excel_file(file_path)
        return list(excel_data.keys())
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        cache_key = self._generate_cache_key(file_path)
        
        # 如果缓存中有信息，直接返回
        if cache_key in self._file_info_cache:
            return self._file_info_cache[cache_key]
        
        # 否则加载文件以获取信息
        self.load_excel_file(file_path)
        return self._file_info_cache.get(cache_key, {})
    
    def detect_columns(self, data: pd.DataFrame) -> Dict[str, List[str]]:
        """
        检测数据列类型
        
        Args:
            data: 数据框
            
        Returns:
            Dict[str, List[str]]: 列类型分类
        """
        numeric_columns = []
        text_columns = []
        datetime_columns = []
        boolean_columns = []
        
        for column in data.columns:
            # 跳过空列
            if data[column].dropna().empty:
                continue
            
            # 尝试转换为数值类型
            try:
                pd.to_numeric(data[column], errors='raise')
                numeric_columns.append(column)
                continue
            except:
                pass
            
            # 检查日期类型
            try:
                pd.to_datetime(data[column], errors='raise')
                datetime_columns.append(column)
                continue
            except:
                pass
            
            # 检查布尔类型
            unique_values = data[column].dropna().unique()
            if len(unique_values) <= 2 and all(
                str(v).lower() in ['true', 'false', '是', '否', 'yes', 'no', '1', '0']
                for v in unique_values
            ):
                boolean_columns.append(column)
                continue
            
            # 默认为文本类型
            text_columns.append(column)
        
        return {
            'numeric': numeric_columns,
            'text': text_columns,
            'datetime': datetime_columns,
            'boolean': boolean_columns,
            'all': list(data.columns)
        }
    
    def validate_required_fields(self, data: pd.DataFrame, required_fields: List[str]) -> Tuple[bool, List[str]]:
        """
        验证必需字段
        
        Args:
            data: 数据框
            required_fields: 必需字段列表
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 缺失字段列表)
        """
        available_columns = set(data.columns)
        missing_fields = []
        
        for field in required_fields:
            if field not in available_columns:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    def clear_cache(self, file_path: Optional[str] = None):
        """
        清除缓存
        
        Args:
            file_path: 指定文件路径，如果为None则清除所有缓存
        """
        if file_path:
            cache_key = self._generate_cache_key(file_path)
            if cache_key in self._cache:
                del self._cache[cache_key]
            if cache_key in self._file_info_cache:
                del self._file_info_cache[cache_key]
            logger.info(f"清除文件缓存: {file_path}")
        else:
            self._cache.clear()
            self._file_info_cache.clear()
            logger.info("清除所有缓存")
    
    def _generate_cache_key(self, file_path: str) -> str:
        """
        生成缓存键
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 缓存键
        """
        # 使用文件路径和修改时间生成唯一键
        full_path = os.path.join(self.upload_folder, file_path)
        if os.path.exists(full_path):
            mtime = os.path.getmtime(full_path)
            key_string = f"{file_path}_{mtime}"
        else:
            key_string = file_path
        
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _validate_excel_data(self, excel_data: Dict[str, pd.DataFrame]):
        """
        验证Excel数据
        
        Args:
            excel_data: Excel数据字典
            
        Raises:
            DataValidationError: 数据验证失败
        """
        if not excel_data:
            raise DataValidationError("Excel文件为空")
        
        # 检查每个工作表
        empty_sheets = []
        for sheet_name, df in excel_data.items():
            if df.empty:
                empty_sheets.append(sheet_name)
            elif len(df.columns) == 0:
                raise DataValidationError(
                    f"工作表'{sheet_name}'没有列",
                    {'sheet_name': sheet_name}
                )
        
        if empty_sheets:
            logger.warning(f"以下工作表为空: {empty_sheets}")
    
    def _clean_excel_data(self, excel_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        清理Excel数据
        
        Args:
            excel_data: 原始Excel数据
            
        Returns:
            Dict[str, pd.DataFrame]: 清理后的数据
        """
        cleaned_data = {}
        
        for sheet_name, df in excel_data.items():
            # 清理列名
            df.columns = [
                str(col).strip() if col is not None else f'未命名列_{i}'
                for i, col in enumerate(df.columns)
            ]
            
            # 移除完全空的行
            df = df.dropna(how='all')
            
            # 移除完全空的列
            df = df.dropna(axis=1, how='all')
            
            cleaned_data[sheet_name] = df
        
        return cleaned_data
    
    def _cache_file_info(self, file_path: str, excel_data: Dict[str, pd.DataFrame]):
        """
        缓存文件信息
        
        Args:
            file_path: 文件路径
            excel_data: Excel数据
        """
        cache_key = self._generate_cache_key(file_path)
        
        sheets_info = []
        for sheet_name, df in excel_data.items():
            column_types = self.detect_columns(df)
            sheets_info.append({
                'name': sheet_name,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'column_types': column_types
            })
        
        self._file_info_cache[cache_key] = {
            'file_path': file_path,
            'sheet_count': len(excel_data),
            'sheets': sheets_info
        }