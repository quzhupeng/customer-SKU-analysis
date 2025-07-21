"""
自定义异常类
Custom Exception Classes

定义应用程序中使用的各种异常类
"""

class AnalysisError(Exception):
    """分析相关异常基类"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DataValidationError(AnalysisError):
    """数据验证异常"""
    pass

class FileProcessingError(AnalysisError):
    """文件处理异常"""
    pass

class ConfigurationError(AnalysisError):
    """配置异常"""
    pass

class FieldMappingError(AnalysisError):
    """字段映射异常"""
    pass

class QuadrantAnalysisError(AnalysisError):
    """四象限分析异常"""
    pass

class ParetoAnalysisError(AnalysisError):
    """帕累托分析异常"""
    pass

class DistributionAnalysisError(AnalysisError):
    """分布分析异常"""
    pass

class DataLoadError(AnalysisError):
    """数据加载异常"""
    pass

class UnitConversionError(AnalysisError):
    """单位转换异常"""
    pass

class SessionNotFoundError(AnalysisError):
    """会话未找到异常"""
    pass

class InvalidAnalysisTypeError(AnalysisError):
    """无效分析类型异常"""
    pass