#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品客户价值分析系统 - 重构版主应用
Product Customer Value Analysis System - Refactored Main Application

重构特性：
- 模块化架构
- 统一异常处理
- 服务层分离
- 工厂模式
- 更好的代码组织

Author: Refactored Version
Date: 2025-01-21
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import pandas as pd
from datetime import datetime
import uuid
import logging

# 导入重构后的模块
from services import DataService, AnalysisService
from utils.error_handlers import register_error_handlers
from utils.exceptions import FileProcessingError, DataValidationError, AnalysisError
from analyzers import AnalyzerFactory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """
    应用工厂函数
    
    Args:
        config: 配置对象（可选）
        
    Returns:
        Flask: 配置好的Flask应用实例
    """
    app = Flask(__name__)
    
    # 应用配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['EXPORT_FOLDER'] = os.environ.get('EXPORT_FOLDER', 'exports')
    app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
    
    # 如果提供了配置对象，更新配置
    if config:
        app.config.update(config)
    
    # 创建必要的文件夹
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 初始化服务
    data_service = DataService(app.config['UPLOAD_FOLDER'])
    analysis_service = AnalysisService(data_service)
    
    # 存储分析结果（在生产环境中应该使用数据库或缓存）
    analysis_results = {}
    
    @app.route('/')
    def index():
        """主页面"""
        return render_template('index.html')
    
    @app.route('/test')
    def test_page():
        """测试页面"""
        return render_template('test.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """处理文件上传"""
        if 'file' not in request.files:
            raise DataValidationError('没有选择文件')
        
        file = request.files['file']
        if file.filename == '':
            raise DataValidationError('没有选择文件')
        
        # 检查文件扩展名
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            raise DataValidationError(
                '不支持的文件格式，请上传Excel文件',
                {'allowed_extensions': list(app.config['ALLOWED_EXTENSIONS'])}
            )
        
        # 生成安全的文件名
        filename = generate_safe_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 保存文件
        logger.info(f"保存上传文件: {filename}")
        file.save(filepath)
        
        # 生成文件ID
        file_id = str(uuid.uuid4())
        
        try:
            # 加载文件信息
            file_info = data_service.get_file_info(filename)
            
            # 存储文件信息
            analysis_results[file_id] = {
                'filename': filename,
                'original_filename': file.filename,
                'upload_time': datetime.now().isoformat(),
                'file_info': file_info
            }
            
            return jsonify({
                'file_id': file_id,
                'sheets': file_info['sheets']
            })
            
        except Exception as e:
            # 如果处理失败，删除文件
            if os.path.exists(filepath):
                os.remove(filepath)
            raise FileProcessingError(f"文件处理失败: {str(e)}")
    
    @app.route('/detect_fields', methods=['POST'])
    def detect_fields():
        """检测字段映射"""
        data = request.get_json()
        
        if not data or 'file_id' not in data or 'sheet_name' not in data:
            raise DataValidationError('缺少必要参数: file_id 或 sheet_name')
        
        file_id = data['file_id']
        sheet_name = data['sheet_name']
        
        # 获取文件信息
        if file_id not in analysis_results:
            raise DataValidationError('无效的文件ID')
        
        filename = analysis_results[file_id]['filename']
        
        # 获取数据
        sheet_data = data_service.get_sheet_data(filename, sheet_name)
        
        # 检测列类型
        column_types = data_service.detect_columns(sheet_data)
        
        # 获取字段建议（如果提供了分析类型）
        suggestions = {}
        if 'analysis_type' in data:
            suggestions = analysis_service.get_field_suggestions(
                filename, sheet_name, data['analysis_type']
            )
        
        return jsonify({
            'columns': list(sheet_data.columns),
            'column_types': column_types,
            'suggestions': suggestions.get('suggestions', {})
        })
    
    @app.route('/analyze', methods=['POST'])
    def analyze():
        """执行数据分析"""
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['file_id', 'sheet_name', 'analysis_type', 'field_mapping']
        for field in required_fields:
            if field not in data:
                raise DataValidationError(f'缺少必需参数: {field}')
        
        file_id = data['file_id']
        sheet_name = data['sheet_name']
        analysis_type = data['analysis_type']
        field_mapping = data['field_mapping']
        
        # 获取文件信息
        if file_id not in analysis_results:
            raise DataValidationError('无效的文件ID')
        
        filename = analysis_results[file_id]['filename']
        
        # 执行分析
        analysis_result = analysis_service.perform_analysis(
            file_id=filename,
            sheet_name=sheet_name,
            analysis_type=analysis_type,
            field_mapping=field_mapping,
            analysis_params=data.get('analysis_params', {})
        )
        
        # 存储分析结果
        if 'analysis_results' not in analysis_results[file_id]:
            analysis_results[file_id]['analysis_results'] = {}
        
        analysis_results[file_id]['analysis_results'][analysis_type] = analysis_result
        
        return jsonify(analysis_result)
    
    @app.route('/export', methods=['POST'])
    def export_report():
        """导出分析报告"""
        data = request.get_json()
        
        if not data or 'file_id' not in data:
            raise DataValidationError('缺少必需参数: file_id')
        
        file_id = data['file_id']
        
        if file_id not in analysis_results:
            raise DataValidationError('无效的文件ID')
        
        # 获取分析结果
        file_data = analysis_results[file_id]
        
        if 'analysis_results' not in file_data:
            raise DataValidationError('没有可导出的分析结果')
        
        # 创建导出文件
        try:
            export_filename = create_export_file(
                file_data, 
                app.config['EXPORT_FOLDER'],
                chart_image=data.get('chart_image')
            )
            
            return send_file(
                os.path.join(app.config['EXPORT_FOLDER'], export_filename),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'分析报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            
        except Exception as e:
            logger.error(f"导出失败: {str(e)}")
            raise AnalysisError(f"导出失败: {str(e)}")
    
    @app.route('/available_analyzers', methods=['GET'])
    def get_available_analyzers():
        """获取可用的分析器类型"""
        analyzers = AnalyzerFactory.get_available_analyzers()
        
        # 添加分析器描述
        analyzer_info = {
            'quadrant': {
                'name': '四象限分析',
                'description': '基于价值和数量维度的四象限分类分析',
                'required_fields': ['value', 'quantity', 'group']
            },
            'pareto': {
                'name': '帕累托分析',
                'description': '80/20法则分析，识别关键因素',
                'required_fields': ['value', 'group']
            },
            'cost_rate_distribution': {
                'name': '成本率分布',
                'description': '分析成本率的分布情况',
                'required_fields': ['cost', 'revenue']
            },
            'price_distribution': {
                'name': '价格分布',
                'description': '分析价格的分布情况',
                'required_fields': ['price', 'quantity']
            },
            'margin_distribution': {
                'name': '利润率分布',
                'description': '分析利润率的分布情况',
                'required_fields': ['revenue', 'cost']
            }
        }
        
        result = []
        for analyzer in analyzers:
            if analyzer in analyzer_info:
                result.append({
                    'type': analyzer,
                    **analyzer_info[analyzer]
                })
        
        return jsonify({'analyzers': result})
    
    @app.route('/analysis_history', methods=['GET'])
    def get_analysis_history():
        """获取分析历史"""
        limit = request.args.get('limit', 10, type=int)
        history = analysis_service.get_analysis_history(limit)
        
        return jsonify({'history': history})
    
    return app


def allowed_file(filename, allowed_extensions):
    """
    检查文件扩展名是否允许
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合
        
    Returns:
        bool: 是否允许
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_safe_filename(original_filename):
    """
    生成安全的文件名
    
    Args:
        original_filename: 原始文件名
        
    Returns:
        str: 安全的文件名
    """
    # 获取文件扩展名
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'xlsx'
    
    # 生成时间戳和UUID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    # 尝试保留原始文件名的一部分
    filename = secure_filename(original_filename)
    if filename and filename != '' and filename != f'.{ext}':
        # 移除扩展名
        name_part = filename.rsplit('.', 1)[0] if '.' in filename else filename
        # 限制长度
        name_part = name_part[:30] if len(name_part) > 30 else name_part
        return f"{timestamp}_{name_part}_{unique_id}.{ext}"
    else:
        return f"{timestamp}_file_{unique_id}.{ext}"


def create_export_file(file_data, export_folder, chart_image=None):
    """
    创建导出文件
    
    Args:
        file_data: 文件数据
        export_folder: 导出文件夹
        chart_image: 图表图片（可选）
        
    Returns:
        str: 导出文件名
    """
    # 这里应该实现实际的导出逻辑
    # 现在只是一个占位实现
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_filename = f"export_{timestamp}.xlsx"
    
    # TODO: 实现导出逻辑
    # 1. 创建Excel文件
    # 2. 写入分析结果
    # 3. 如果有图表图片，插入到Excel中
    
    return export_filename


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)