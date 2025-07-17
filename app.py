#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品客户价值分析系统 - 主应用文件
Product Customer Value Analysis System - Main Application

Author: Augment Agent
Date: 2025-07-15
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

# 导入自定义模块
from analyzer import DataAnalyzer
from utils import allowed_file, create_upload_folder

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 应用配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EXPORT_FOLDER'] = 'exports'

# 创建必要的文件夹
create_upload_folder(app.config['UPLOAD_FOLDER'])
create_upload_folder(app.config['EXPORT_FOLDER'])

# 全局变量存储分析结果
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
    """
    处理文件上传
    返回: JSON格式的响应，包含sheet列表或错误信息
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，请上传.xlsx或.xls文件'}), 400
        
        # 保存文件
        original_filename = file.filename
        logger.info(f"原始文件名: {original_filename}")

        filename = secure_filename(original_filename)
        logger.info(f"secure_filename处理后: {filename}")

        # 处理secure_filename可能返回空字符串或无效字符的情况
        if not filename or filename.strip() in ['', '-', '_', '.'] or len(filename.strip()) == 0:
            # 如果secure_filename处理后为空或无效，使用默认名称
            file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'xlsx'
            filename = f"uploaded_file.{file_ext}"
            logger.info(f"使用默认文件名: {filename}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        logger.info(f"最终文件路径: {filepath}")

        # 确保上传目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        
        # 读取Excel文件获取sheet列表
        try:
            excel_file = pd.ExcelFile(filepath)
            sheets = excel_file.sheet_names
            
            # 存储文件信息到session或临时存储
            file_info = {
                'filepath': filepath,
                'original_filename': filename,
                'sheets': sheets,
                'upload_time': datetime.now().isoformat()
            }
            
            # 生成唯一的文件ID
            file_id = str(uuid.uuid4())
            analysis_results[file_id] = {'file_info': file_info}
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'sheets': sheets,
                'message': '文件上传成功'
            })
            
        except Exception as e:
            logger.error(f"读取Excel文件失败: {str(e)}")
            return jsonify({'error': f'读取Excel文件失败: {str(e)}'}), 400
            
    except RequestEntityTooLarge:
        return jsonify({'error': '文件太大，请上传小于50MB的文件'}), 413
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return jsonify({'error': f'文件上传失败: {str(e)}'}), 500

@app.route('/field_detection', methods=['POST'])
def detect_fields():
    """
    字段检测接口
    接收: file_id, sheet_name
    返回: 检测到的字段信息
    """
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        sheet_name = data.get('sheet_name')
        
        if not all([file_id, sheet_name]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        if file_id not in analysis_results:
            return jsonify({'error': '文件信息不存在'}), 400
        
        file_info = analysis_results[file_id]['file_info']
        filepath = file_info['filepath']
        
        # 创建分析器并检测字段
        analyzer = DataAnalyzer(filepath, sheet_name)
        field_info = analyzer.detect_fields()
        
        return jsonify({
            'success': True,
            'fields': field_info,
            'message': '字段检测完成'
        })
        
    except Exception as e:
        logger.error(f"字段检测失败: {str(e)}")
        return jsonify({'error': f'字段检测失败: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze_data():
    """
    执行数据分析
    接收: file_id, sheet_name, analysis_type, unit_confirmations, pareto_dimension
    返回: 分析结果的JSON数据
    """
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        sheet_name = data.get('sheet_name')
        analysis_type = data.get('analysis_type')  # 'product', 'customer', 'region'
        unit_confirmations = data.get('unit_confirmations', {})
        pareto_dimension = data.get('pareto_dimension')  # 'profit', 'amount', 'quantity'

        if not all([file_id, sheet_name, analysis_type]):
            return jsonify({'error': '缺少必要参数'}), 400

        if file_id not in analysis_results:
            return jsonify({'error': '文件信息不存在，请重新上传'}), 400

        file_info = analysis_results[file_id]['file_info']
        filepath = file_info['filepath']

        # 创建数据分析器
        analyzer = DataAnalyzer(filepath, sheet_name)

        # 执行分析
        result = analyzer.analyze(analysis_type, unit_confirmations, pareto_dimension)

        # 存储分析结果
        analysis_results[file_id]['analysis_result'] = result
        analysis_results[file_id]['analysis_type'] = analysis_type
        analysis_results[file_id]['unit_confirmations'] = unit_confirmations
        analysis_results[file_id]['pareto_dimension'] = pareto_dimension

        return jsonify({
            'success': True,
            'data': result,
            'message': '分析完成'
        })

    except Exception as e:
        logger.error(f"数据分析失败: {str(e)}")
        return jsonify({'error': f'数据分析失败: {str(e)}'}), 500

@app.route('/pareto-dimensions', methods=['POST'])
def get_pareto_dimensions():
    """
    获取可用的帕累托分析维度
    接收: file_id, sheet_name, analysis_type
    返回: 可用维度列表
    """
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        sheet_name = data.get('sheet_name')
        analysis_type = data.get('analysis_type')

        if not all([file_id, sheet_name, analysis_type]):
            return jsonify({'error': '缺少必要参数'}), 400

        if file_id not in analysis_results:
            return jsonify({'error': '文件信息不存在，请重新上传'}), 400

        file_info = analysis_results[file_id]['file_info']
        filepath = file_info['filepath']

        # 创建数据分析器
        analyzer = DataAnalyzer(filepath, sheet_name)

        # 检测字段
        analyzer.detect_fields()

        # 获取可用维度
        available_dimensions = analyzer._get_available_pareto_dimensions(analysis_type)

        # 获取维度信息
        dimensions_info = []
        for dim in available_dimensions:
            info = analyzer._get_pareto_dimension_info(dim, analysis_type)
            dimensions_info.append({
                'value': dim,
                'name': info['name'],
                'unit': info['unit'],
                'description': info['description']
            })

        return jsonify({
            'success': True,
            'data': {
                'available_dimensions': available_dimensions,
                'dimensions_info': dimensions_info
            }
        })

    except Exception as e:
        logger.error(f"获取帕累托维度失败: {str(e)}")
        return jsonify({'error': f'获取帕累托维度失败: {str(e)}'}), 500

@app.route('/export', methods=['POST'])
def export_report():
    """
    导出Excel报告
    接收: file_id
    返回: Excel文件下载
    """
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id or file_id not in analysis_results:
            return jsonify({'error': '分析结果不存在'}), 400
        
        result_data = analysis_results[file_id]
        
        # 创建导出器并生成Excel报告
        from exporter import ReportExporter
        exporter = ReportExporter(result_data)
        
        # 生成导出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_filename = f"分析报告_{timestamp}.xlsx"
        export_path = os.path.join(app.config['EXPORT_FOLDER'], export_filename)
        
        # 生成Excel文件
        exporter.export_to_excel(export_path)
        
        return send_file(
            export_path,
            as_attachment=True,
            download_name=export_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"导出报告失败: {str(e)}")
        return jsonify({'error': f'导出报告失败: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {str(error)}")
    return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return jsonify({'error': '文件太大，请上传小于50MB的文件'}), 413

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
