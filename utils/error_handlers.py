"""
错误处理器
Error Handlers

提供统一的错误处理机制
"""

from flask import jsonify, current_app
from .exceptions import (
    AnalysisError, DataValidationError, FileProcessingError,
    ConfigurationError, SessionNotFoundError
)
import traceback
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    注册错误处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(DataValidationError)
    def handle_data_validation_error(error):
        """处理数据验证错误"""
        logger.error(f"数据验证错误: {error.message}")
        return jsonify({
            'error': error.message,
            'type': 'data_validation_error',
            'details': error.details
        }), 400
    
    @app.errorhandler(FileProcessingError)
    def handle_file_processing_error(error):
        """处理文件处理错误"""
        logger.error(f"文件处理错误: {error.message}")
        return jsonify({
            'error': error.message,
            'type': 'file_processing_error',
            'details': error.details
        }), 400
    
    @app.errorhandler(ConfigurationError)
    def handle_configuration_error(error):
        """处理配置错误"""
        logger.error(f"配置错误: {error.message}")
        return jsonify({
            'error': error.message,
            'type': 'configuration_error',
            'details': error.details
        }), 500
    
    @app.errorhandler(SessionNotFoundError)
    def handle_session_not_found(error):
        """处理会话未找到错误"""
        logger.warning(f"会话未找到: {error.message}")
        return jsonify({
            'error': error.message,
            'type': 'session_not_found',
            'details': error.details
        }), 404
    
    @app.errorhandler(AnalysisError)
    def handle_analysis_error(error):
        """处理分析错误（通用）"""
        logger.error(f"分析错误: {error.message}")
        return jsonify({
            'error': error.message,
            'type': 'analysis_error',
            'details': error.details
        }), 400
    
    @app.errorhandler(FileNotFoundError)
    def handle_file_not_found(error):
        """处理文件未找到错误"""
        logger.error(f"文件未找到: {str(error)}")
        return jsonify({
            'error': '请求的文件不存在',
            'type': 'file_not_found'
        }), 404
    
    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """处理值错误"""
        logger.error(f"值错误: {str(error)}")
        return jsonify({
            'error': str(error),
            'type': 'value_error'
        }), 400
    
    @app.errorhandler(KeyError)
    def handle_key_error(error):
        """处理键错误"""
        logger.error(f"键错误: {str(error)}")
        return jsonify({
            'error': f'缺少必需的字段: {str(error)}',
            'type': 'key_error'
        }), 400
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """处理未预期的错误"""
        logger.error(f"未预期错误: {str(error)}")
        logger.error(traceback.format_exc())
        
        # 在调试模式下返回详细错误信息
        if current_app.debug:
            return jsonify({
                'error': str(error),
                'type': 'unexpected_error',
                'traceback': traceback.format_exc()
            }), 500
        else:
            return jsonify({
                'error': '服务器内部错误，请稍后重试',
                'type': 'internal_server_error'
            }), 500
    
    @app.errorhandler(404)
    def handle_404(error):
        """处理404错误"""
        logger.warning(f"404错误: {error}")
        return jsonify({
            'error': '请求的资源不存在',
            'type': 'not_found'
        }), 404
    
    @app.errorhandler(405)
    def handle_405(error):
        """处理405错误"""
        logger.warning(f"405错误: {error}")
        return jsonify({
            'error': '不支持的请求方法',
            'type': 'method_not_allowed'
        }), 405
    
    @app.errorhandler(413)
    def handle_413(error):
        """处理413错误（请求实体过大）"""
        logger.warning(f"413错误: {error}")
        return jsonify({
            'error': '上传的文件过大',
            'type': 'request_entity_too_large'
        }), 413

def safe_execute(func, *args, error_message="操作失败", **kwargs):
    """
    安全执行函数，捕获异常并返回友好错误信息
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        error_message: 默认错误消息
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果或None（如果出错）
        
    Raises:
        AnalysisError: 如果执行失败
    """
    try:
        return func(*args, **kwargs)
    except AnalysisError:
        # 重新抛出自定义异常
        raise
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}")
        logger.error(traceback.format_exc())
        raise AnalysisError(error_message, {'original_error': str(e)})