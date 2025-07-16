// 全局变量
let currentFileId = null;
let currentSheetName = null;
let currentAnalysisType = null;
let currentParetoDimension = null;
let availableParetoDimensions = [];
let analysisResult = null;
let chartInstances = {}; // 存储图表实例

// DOM元素
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const sheetSection = document.getElementById('sheetSection');
const sheetList = document.getElementById('sheetList');
const fieldSection = document.getElementById('fieldSection');
const unitSection = document.getElementById('unitSection');
const analysisSection = document.getElementById('analysisSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const messageContainer = document.getElementById('messageContainer');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

// 初始化事件监听器
function initializeEventListeners() {
    // 文件上传
    fileInput.addEventListener('change', handleFileSelect);
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // 下一步按钮
    document.getElementById('nextToFieldDetection').addEventListener('click', handleFieldDetection);
    document.getElementById('nextToUnitConfirmation').addEventListener('click', handleUnitConfirmation);
    document.getElementById('startAnalysis').addEventListener('click', handleStartAnalysis);
    
    // 分析类型选择
    document.querySelectorAll('input[name="analysisType"]').forEach(radio => {
        radio.addEventListener('change', handleAnalysisTypeChange);
    });
    
    // 导出和新建分析
    document.getElementById('exportReport').addEventListener('click', handleExportReport);
    document.getElementById('newAnalysis').addEventListener('click', handleNewAnalysis);
}

// 文件选择处理
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

// 拖拽处理
function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

// 文件上传
async function uploadFile(file) {
    // 验证文件类型
    const allowedTypes = ['.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showMessage('请上传Excel文件（.xlsx或.xls格式）', 'error');
        return;
    }
    
    // 验证文件大小
    if (file.size > 50 * 1024 * 1024) {
        showMessage('文件大小不能超过50MB', 'error');
        return;
    }
    
    // 显示上传进度
    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = '上传中...';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            progressFill.style.width = '100%';
            progressText.textContent = '上传完成';
            
            currentFileId = result.file_id;
            showSheetSelection(result.sheets);
            showMessage('文件上传成功', 'success');
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        showMessage('上传失败: ' + error.message, 'error');
        uploadProgress.style.display = 'none';
    }
}

// 显示Sheet选择
function showSheetSelection(sheets) {
    sheetList.innerHTML = '';
    
    sheets.forEach(sheet => {
        const sheetItem = document.createElement('div');
        sheetItem.className = 'sheet-item';
        sheetItem.textContent = sheet;
        sheetItem.addEventListener('click', () => selectSheet(sheet, sheetItem));
        sheetList.appendChild(sheetItem);
    });
    
    sheetSection.style.display = 'block';
}

// 选择Sheet
function selectSheet(sheetName, element) {
    // 移除其他选中状态
    document.querySelectorAll('.sheet-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // 设置当前选中
    element.classList.add('selected');
    currentSheetName = sheetName;
    
    // 启用下一步按钮
    document.getElementById('nextToFieldDetection').disabled = false;
}

// 字段检测处理
async function handleFieldDetection() {
    if (!currentFileId || !currentSheetName) {
        showMessage('请先选择工作表', 'error');
        return;
    }
    
    showLoading('检测字段中...');
    
    try {
        const response = await fetch('/field_detection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet_name: currentSheetName
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayFieldDetectionResult(result.fields);
            fieldSection.style.display = 'block';
            hideLoading();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        hideLoading();
        showMessage('字段检测失败: ' + error.message, 'error');
    }
}

// 显示字段检测结果
function displayFieldDetectionResult(fields) {
    const resultContainer = document.getElementById('fieldDetectionResult');
    
    const detectedFields = fields.detected_fields;
    const columnInfo = fields.column_info;
    
    let html = '<h4>检测到的关键字段:</h4>';
    
    const fieldLabels = {
        'product': '产品字段',
        'customer': '客户字段',
        'region': '地区字段',
        'quantity': '数量字段',
        'profit': '毛利字段',
        'amount': '金额字段'
    };
    
    Object.entries(fieldLabels).forEach(([fieldType, label]) => {
        const column = detectedFields[fieldType];
        const status = column ? 'found' : 'missing';
        const statusText = column ? `已找到: ${column}` : '未找到';

        // 为未找到的字段提供建议
        let suggestion = '';
        if (!column) {
            const suggestions = {
                'product': '请确保数据中包含产品名称、SKU、物料名称等列',
                'customer': '请确保数据中包含客户名称、客户等列',
                'region': '请确保数据中包含地区、区域、省份等列',
                'quantity': '请确保数据中包含数量、销量、重量等列',
                'profit': '请确保数据中包含毛利、利润等列',
                'amount': '请确保数据中包含金额、销售额等列'
            };
            suggestion = `<br><small style="color: #999;">${suggestions[fieldType]}</small>`;
        }

        html += `
            <div class="field-item">
                <span>${label}</span>
                <span class="field-status ${status}">${statusText}${suggestion}</span>
            </div>
        `;
    });
    
    html += `<p style="margin-top: 15px; color: #666;">
        数据行数: ${fields.total_rows} | 列数: ${fields.total_columns}
    </p>`;

    // 显示所有列名和识别结果
    html += '<h5 style="margin-top: 20px;">所有列名识别结果:</h5>';
    html += '<div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9;">';

    Object.entries(columnInfo).forEach(([columnName, info]) => {
        const fieldType = info.field_type;
        const isRecognized = fieldType !== 'unknown';
        const statusColor = isRecognized ? '#28a745' : '#6c757d';
        const statusText = isRecognized ? `识别为: ${fieldType}` : '未识别';

        html += `
            <div style="margin-bottom: 5px; padding: 5px; border-left: 3px solid ${statusColor};">
                <strong>${columnName}</strong>
                <span style="color: ${statusColor}; font-size: 0.9em;">(${statusText})</span>
                <br><small style="color: #666;">样本值: ${info.sample_values.join(', ')}</small>
            </div>
        `;
    });

    html += '</div>';
    
    resultContainer.innerHTML = html;
}

// 分析类型变更处理
function handleAnalysisTypeChange(event) {
    currentAnalysisType = event.target.value;
    document.getElementById('nextToUnitConfirmation').disabled = false;
}

// 单位确认处理
function handleUnitConfirmation() {
    if (!currentAnalysisType) {
        showMessage('请先选择分析类型', 'error');
        return;
    }
    
    displayUnitOptions();
    unitSection.style.display = 'block';
}

// 显示单位选项
function displayUnitOptions() {
    const unitOptions = document.getElementById('unitOptions');
    
    const html = `
        <div class="unit-group">
            <h4><i class="fas fa-weight"></i> 数量字段单位确认</h4>
            <p>您上传的"数量"字段的原始单位是？</p>
            <div class="unit-radio-group">
                <label class="unit-radio">
                    <input type="radio" name="quantityUnit" value="kg" checked>
                    <span>千克 (kg)</span>
                </label>
                <label class="unit-radio">
                    <input type="radio" name="quantityUnit" value="t">
                    <span>吨 (t)</span>
                </label>
            </div>
        </div>
        
        <div class="unit-group">
            <h4><i class="fas fa-dollar-sign"></i> 金额/毛利字段单位确认</h4>
            <p>您上传的"毛利"、"金额"字段的原始单位是？</p>
            <div class="unit-radio-group">
                <label class="unit-radio">
                    <input type="radio" name="amountUnit" value="yuan" checked>
                    <span>元</span>
                </label>
                <label class="unit-radio">
                    <input type="radio" name="amountUnit" value="wan_yuan">
                    <span>万元</span>
                </label>
            </div>
        </div>
    `;
    
    unitOptions.innerHTML = html;
    
    // 启用开始分析按钮
    document.getElementById('startAnalysis').disabled = false;
}

// 开始分析处理
async function handleStartAnalysis() {
    const quantityUnit = document.querySelector('input[name="quantityUnit"]:checked').value;
    const amountUnit = document.querySelector('input[name="amountUnit"]:checked').value;

    const unitConfirmations = {
        quantity: quantityUnit,
        amount: amountUnit
    };

    showLoading('获取分析选项中...');

    try {
        // 首先获取可用的帕累托维度
        await loadParetoDimensions();

        showLoading('分析数据中，请稍候...');

        // 使用默认维度进行初始分析
        const defaultDimension = availableParetoDimensions.length > 0 ? availableParetoDimensions[0].value : null;
        currentParetoDimension = defaultDimension;

        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet_name: currentSheetName,
                analysis_type: currentAnalysisType,
                unit_confirmations: unitConfirmations,
                pareto_dimension: currentParetoDimension
            })
        });

        const result = await response.json();

        if (result.success) {
            analysisResult = result.data;
            displayAnalysisResults();
            analysisSection.style.display = 'block';
            hideLoading();
            showMessage('分析完成', 'success');

            // 初始化帕累托维度选择器
            initializeParetoDimensionSelector();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        hideLoading();
        showMessage('分析失败: ' + error.message, 'error');
    }
}

// 加载帕累托分析维度
async function loadParetoDimensions() {
    try {
        const response = await fetch('/pareto-dimensions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet_name: currentSheetName,
                analysis_type: currentAnalysisType
            })
        });

        const result = await response.json();

        if (result.success) {
            availableParetoDimensions = result.data.dimensions_info;
        } else {
            console.error('获取帕累托维度失败:', result.error);
            availableParetoDimensions = [];
        }
    } catch (error) {
        console.error('获取帕累托维度失败:', error);
        availableParetoDimensions = [];
    }
}

// 初始化帕累托维度选择器
function initializeParetoDimensionSelector() {
    const selector = document.getElementById('paretoDimensionSelect');
    if (!selector) return;

    // 清空现有选项
    selector.innerHTML = '';

    // 添加选项
    availableParetoDimensions.forEach(dimension => {
        const option = document.createElement('option');
        option.value = dimension.value;
        option.textContent = `${dimension.name}(${dimension.unit})`;
        option.title = dimension.description;

        // 设置默认选中
        if (dimension.value === currentParetoDimension) {
            option.selected = true;
        }

        selector.appendChild(option);
    });

    // 添加事件监听器
    selector.addEventListener('change', handleParetoDimensionChange);
}

// 处理帕累托维度变更
async function handleParetoDimensionChange(event) {
    const newDimension = event.target.value;
    if (newDimension === currentParetoDimension) return;

    currentParetoDimension = newDimension;

    showLoading('重新分析帕累托数据...');

    try {
        // 重新进行分析
        const quantityUnit = document.querySelector('input[name="quantityUnit"]:checked').value;
        const amountUnit = document.querySelector('input[name="amountUnit"]:checked').value;

        const unitConfirmations = {
            quantity: quantityUnit,
            amount: amountUnit
        };

        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet_name: currentSheetName,
                analysis_type: currentAnalysisType,
                unit_confirmations: unitConfirmations,
                pareto_dimension: currentParetoDimension
            })
        });

        const result = await response.json();

        if (result.success) {
            analysisResult = result.data;
            // 只更新帕累托图表
            displayParetoChart();
            hideLoading();
            showMessage('帕累托分析已更新', 'success');
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        hideLoading();
        showMessage('更新帕累托分析失败: ' + error.message, 'error');
    }
}

// 显示分析结果
function displayAnalysisResults() {
    if (!analysisResult) return;
    
    // 显示四象限分析
    displayQuadrantAnalysis();
    
    // 显示策略卡片
    displayStrategyCards();
    
    // 显示补充图表
    displayAdditionalCharts();
    
    // 显示数据表格
    displayDataTable();

    // 确保图表正确显示
    setTimeout(resizeCharts, 300);
}

// 显示四象限分析
function displayQuadrantAnalysis() {
    const quadrantData = analysisResult.quadrant_analysis;
    const chartContainer = document.getElementById('quadrantChart');

    console.log('displayQuadrantAnalysis 调试信息:');
    console.log('- 四象限数据点数量:', quadrantData.scatter_data.length);
    console.log('- 当前筛选状态:', isQuadrantFiltered);
    console.log('- 当前筛选类型:', currentFilterType);

    // 获取或创建图表实例
    let chart = chartInstances['quadrantChart'];
    if (!chart || chart.isDisposed()) {
        chart = echarts.init(chartContainer);
        chartInstances['quadrantChart'] = chart;
    } else {
        // 清除现有配置，确保完全重新渲染
        chart.clear();
    }

    // 准备散点数据
    const scatterData = quadrantData.scatter_data.map(item => {
        const xField = getXFieldName();
        const yField = getYFieldName();
        return [item[xField], item[yField], item];
    });

    console.log('- 处理后的散点数据数量:', scatterData.length);
    console.log('- X轴字段:', getXFieldName());
    console.log('- Y轴字段:', getYFieldName());

    // 根据筛选状态设置标题
    let chartTitle = '四象限分析';
    let titleColor = '#333';

    if (isQuadrantFiltered) {
        if (currentFilterType === 'loss') {
            chartTitle = '四象限分析 - 亏损项目';
            titleColor = '#ff6b6b';
        } else if (currentFilterType === 'profitable') {
            chartTitle = '四象限分析 - 盈利项目';
            titleColor = '#4CAF50';
        }
    }

    const option = {
        title: {
            text: chartTitle,
            left: 'center',
            textStyle: {
                color: titleColor
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                const data = params.data[2];
                // 格式化数值，销售金额和毛利贡献不保留小数
                let xValue = params.data[0];
                let yValue = params.data[1];

                // 判断是否为金额或毛利相关字段，不保留小数
                if (quadrantData.x_label.includes('金额') || quadrantData.x_label.includes('毛利')) {
                    xValue = Math.round(xValue);
                }
                if (quadrantData.y_label.includes('金额') || quadrantData.y_label.includes('毛利')) {
                    yValue = Math.round(yValue);
                }

                return `${getGroupFieldName()}: ${data[getGroupFieldName()]}<br/>
                        ${quadrantData.x_label}: ${xValue}<br/>
                        ${quadrantData.y_label}: ${yValue}<br/>
                        象限: ${data.象限名称}`;
            }
        },
        xAxis: {
            type: 'value',
            name: quadrantData.x_label,
            nameLocation: 'middle',
            nameGap: 30,
            axisLine: {
                lineStyle: {
                    color: '#333'
                }
            }
        },
        yAxis: {
            type: 'value',
            name: quadrantData.y_label,
            nameLocation: 'middle',
            nameGap: 50,
            axisLine: {
                lineStyle: {
                    color: '#333'
                }
            }
        },
        series: [{
            type: 'scatter',
            data: scatterData,
            symbolSize: 8,
            itemStyle: {
                color: function(params) {
                    const quadrant = params.data[2].象限;
                    const colors = {
                        1: '#F44336',  // 红色 - 明星/核心 (高高)
                        2: '#FF9800',  // 橙色 - 潜力/成长 (低高)
                        3: '#9E9E9E',  // 灰色 - 瘦狗/机会 (低低)
                        4: '#4CAF50'   // 绿色 - 金牛/增利 (高低)
                    };
                    return colors[quadrant] || '#666';
                }
            },
            // 添加分割线 - 使用markLine实现
            markLine: {
                silent: true,
                symbol: 'none',
                lineStyle: {
                    color: '#333',
                    type: 'solid',
                    width: 3
                },
                data: [
                    {
                        xAxis: quadrantData.x_avg,
                        name: 'X平均线'
                    },
                    {
                        yAxis: quadrantData.y_avg,
                        name: 'Y平均线'
                    }
                ]
            }
        }]
    };
    
    // 使用 notMerge: true 强制完全重新渲染
    chart.setOption(option, true);
    
    // 点击事件
    chart.on('click', function(params) {
        if (params.componentType === 'series') {
            const data = params.data[2];
            filterTableByItem(data);
        }
    });
}

// 工具函数：获取字段名
function getXFieldName() {
    const fieldMap = {
        'product': analysisResult.field_detection.detected_fields.quantity,
        'customer': analysisResult.field_detection.detected_fields.amount,
        'region': analysisResult.field_detection.detected_fields.amount
    };
    return fieldMap[currentAnalysisType];
}

function getYFieldName() {
    const fieldMap = {
        'product': '吨毛利',
        'customer': analysisResult.field_detection.detected_fields.profit,
        'region': analysisResult.field_detection.detected_fields.profit
    };
    return fieldMap[currentAnalysisType];
}

function getGroupFieldName() {
    // 如果没有分析结果，返回null
    if (!analysisResult || !analysisResult.field_detection) {
        return null;
    }
    
    // 获取原始检测的字段名
    const fieldMap = {
        'product': analysisResult.field_detection.detected_fields.product,
        'customer': analysisResult.field_detection.detected_fields.customer,
        'region': analysisResult.field_detection.detected_fields.region
    };
    
    const originalFieldName = fieldMap[currentAnalysisType];
    
    // 如果没有找到原始字段名，返回null
    if (!originalFieldName) {
        return null;
    }
    
    // 检查数据是否已经被聚合，如果是，可能需要调整字段名
    // 首先尝试使用原始字段名
    if (analysisResult.aggregated_data && analysisResult.aggregated_data.length > 0) {
        const sampleData = analysisResult.aggregated_data[0];
        
        // 如果原始字段名存在于聚合数据中，直接返回
        if (sampleData.hasOwnProperty(originalFieldName)) {
            return originalFieldName;
        }
        
        // 否则，尝试查找可能的替代字段名
        // 聚合后的数据可能会使用不同的字段名，比如索引名或者带有前缀/后缀的名称
        const possibleFields = Object.keys(sampleData);
        
        // 尝试精确匹配（忽略大小写）
        const exactMatch = possibleFields.find(field => 
            field.toLowerCase() === originalFieldName.toLowerCase()
        );
        if (exactMatch) {
            return exactMatch;
        }
        
        // 尝试部分匹配
        // 根据分析类型查找包含关键词的字段
        const keywords = {
            'product': ['产品', 'product', 'sku', '物料', '商品'],
            'customer': ['客户', 'customer', 'client', '买家'],
            'region': ['地区', 'region', '区域', '省份', 'area']
        };
        
        const typeKeywords = keywords[currentAnalysisType] || [];
        for (const keyword of typeKeywords) {
            const matchedField = possibleFields.find(field => 
                field.toLowerCase().includes(keyword.toLowerCase()) &&
                !field.includes('数量') && 
                !field.includes('金额') && 
                !field.includes('毛利') &&
                !field.includes('成本') &&
                !field.includes('占比') &&
                !field.includes('率') &&
                !field.includes('统计')
            );
            if (matchedField) {
                return matchedField;
            }
        }
        
        // 如果还是找不到，检查是否有索引字段（可能被设置为索引）
        if (possibleFields.includes('index')) {
            return 'index';
        }
        
        // 最后尝试找第一个看起来像名称的字段
        const nameField = possibleFields.find(field => 
            (field.includes('名称') || field.includes('name')) &&
            !field.includes('象限')
        );
        if (nameField) {
            return nameField;
        }
    }
    
    // 默认返回原始字段名
    return originalFieldName;
}

function getGroupFieldLabel() {
    const labelMap = {
        'product': '产品名称',
        'customer': '客户名称',
        'region': '地区名称'
    };
    return labelMap[currentAnalysisType] || '名称';
}

// 根据分析类型获取第二个统计组
function getSecondStatGroup(stats) {
    if (currentAnalysisType === 'product') {
        return `
            <div class="stat-group">
                <div class="stat-label">吨毛利(元/吨)</div>
                <div class="stat-value">${stats.ton_profit}</div>
                <div class="stat-value">占比: -</div>
            </div>
        `;
    } else {
        return `
            <div class="stat-group">
                <div class="stat-label">毛利贡献(万元)</div>
                <div class="stat-value">数量: ${stats.profit_sum}</div>
                <div class="stat-value">占比: ${stats.profit_percentage}%</div>
            </div>
        `;
    }
}

// 根据分析类型获取第三个统计组
function getThirdStatGroup(stats) {
    if (currentAnalysisType === 'product') {
        return `
            <div class="stat-group">
                <div class="stat-label">销量(吨)</div>
                <div class="stat-value">数量: ${stats.quantity_sum}</div>
                <div class="stat-value">占比: ${stats.quantity_percentage}%</div>
            </div>
        `;
    } else {
        return `
            <div class="stat-group">
                <div class="stat-label">销售额(万元)</div>
                <div class="stat-value">数量: ${stats.amount_sum}</div>
                <div class="stat-value">占比: ${stats.amount_percentage}%</div>
            </div>
        `;
    }
}

// 显示策略卡片
function displayStrategyCards() {
    const quadrantStats = analysisResult.quadrant_analysis.quadrant_stats;
    const cardsContainer = document.getElementById('strategyCards');

    let html = '';

    [1, 2, 3, 4].forEach(quadrant => {
        const stats = quadrantStats[quadrant];
        const colors = {
            1: '#F44336',  // 红色 - 明星/核心 (高高)
            2: '#FF9800',  // 橙色 - 潜力/成长 (低高)
            3: '#9E9E9E',  // 灰色 - 瘦狗/机会 (低低)
            4: '#4CAF50'   // 绿色 - 金牛/增利 (高低)
        };

        html += `
            <div class="strategy-card" style="border-left-color: ${colors[quadrant]}">
                <h4>${stats.name}</h4>
                <div class="description">${stats.description}</div>
                <div class="stats-info">
                    <div class="stats-row">
                        <div class="stat-group">
                            <div class="stat-label">SKU统计</div>
                            <div class="stat-value">数量: ${stats.count}</div>
                            <div class="stat-value">占比: ${stats.count_percentage}%</div>
                        </div>
                        ${getSecondStatGroup(stats)}
                        ${getThirdStatGroup(stats)}
                    </div>
                </div>
                <div class="strategy">${stats.strategy}</div>
            </div>
        `;
    });

    cardsContainer.innerHTML = html;
}

// 显示补充图表
function displayAdditionalCharts() {
    displayParetoChart();
    displayDistributionChart();
    displayProfitLossChart();
    displayContributionChart();

    // 显示成本分析图表（如果有成本数据）
    if (analysisResult.additional_analysis.cost_analysis) {
        displayCostAnalysisCharts();
        document.getElementById('costAnalysisSection').style.display = 'block';
    } else {
        document.getElementById('costAnalysisSection').style.display = 'none';
    }
}

// 帕累托图
function displayParetoChart() {
    const paretoData = analysisResult.additional_analysis.pareto_analysis;
    const chartContainer = document.getElementById('paretoChart');

    const chart = echarts.init(chartContainer);
    chartInstances['paretoChart'] = chart;

    const data = paretoData.pareto_data.slice(0, 20); // 只显示前20项
    const categories = data.map(item => item[getGroupFieldName()]);
    const values = data.map(item => item.累计占比);

    // 获取维度信息用于显示
    const dimensionInfo = paretoData.dimension_info || { name: '数值', unit: '' };
    const dimensionLabel = dimensionInfo.unit ? `${dimensionInfo.name}(${dimensionInfo.unit})` : dimensionInfo.name;

    const option = {
        title: {
            text: `帕累托分析 - ${dimensionLabel}`,
            left: 'center',
            textStyle: {
                fontSize: 14,
                color: '#333'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            formatter: function(params) {
                const point = params[0];
                const itemData = data[point.dataIndex];
                const fieldName = getGroupFieldName();
                const sortField = paretoData.dimension || 'profit';
                const sortColumn = getSortColumnName(sortField);

                return `
                    <div style="text-align: left;">
                        <strong>${point.name}</strong><br/>
                        累计占比: ${point.value}%<br/>
                        ${dimensionLabel}: ${formatNumber(itemData[sortColumn])}
                    </div>
                `;
            }
        },
        xAxis: {
            type: 'category',
            data: categories,
            axisLabel: {
                rotate: 45,
                interval: 0
            }
        },
        yAxis: {
            type: 'value',
            name: '累计占比(%)',
            max: 100
        },
        series: [{
            type: 'line',
            data: values,
            smooth: true,
            lineStyle: {
                color: '#667eea',
                width: 3
            },
            itemStyle: {
                color: '#667eea'
            },
            markLine: {
                data: [{
                    yAxis: 80,
                    name: '80%线',
                    lineStyle: {
                        color: '#ff4444',
                        type: 'dashed'
                    }
                }]
            }
        }]
    };

    chart.setOption(option);
}

// 获取排序字段的列名
function getSortColumnName(sortField) {
    const fieldMapping = {
        'profit': getFieldName('profit'),
        'amount': getFieldName('amount'),
        'quantity': getFieldName('quantity')
    };
    return fieldMapping[sortField] || sortField;
}

// 获取字段名称
function getFieldName(fieldType) {
    // 根据分析类型和字段类型返回对应的字段名
    const fieldMappings = {
        'product': {
            'profit': '毛利',
            'amount': '销售金额',
            'quantity': '销量'
        },
        'customer': {
            'profit': '毛利贡献',
            'amount': '采购金额',
            'quantity': '采购量'
        },
        'region': {
            'profit': '毛利贡献',
            'amount': '销售金额',
            'quantity': '销量'
        }
    };

    return fieldMappings[currentAnalysisType]?.[fieldType] || fieldType;
}

// 格式化数字显示
function formatNumber(value) {
    if (value === null || value === undefined) return '-';
    if (typeof value !== 'number') return value;

    // 保留2位小数并添加千分位分隔符
    return value.toLocaleString('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

// 分布图 - 升级版：条形图展示价值维度
function displayDistributionChart() {
    const distributionData = analysisResult.additional_analysis.distribution_analysis;
    const chartContainer = document.getElementById('distributionChart');

    const chart = echarts.init(chartContainer);
    chartInstances['distributionChart'] = chart;

    const data = distributionData.interval_data;
    const categories = data.map(item => item.区间);
    const values = data.map(item => item.价值总和);
    const counts = data.map(item => item.项目数量);
    const valuePercentages = data.map(item => item.价值占比);
    const countPercentages = data.map(item => item.数量占比);

    const option = {
        title: {
            text: distributionData.title,
            left: 'center',
            textStyle: {
                fontSize: 16,
                fontWeight: 'bold'
            },
            subtextStyle: {
                fontSize: 12
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                const dataIndex = params[0].dataIndex;
                const interval = categories[dataIndex];
                const value = values[dataIndex];
                const count = counts[dataIndex];
                const valuePercent = valuePercentages[dataIndex];
                const countPercent = countPercentages[dataIndex];
                const avgValue = data[dataIndex].单项平均价值;

                return `
                    <div style="font-weight: bold; margin-bottom: 8px;">${interval}</div>
                    <div style="margin-bottom: 4px;">
                        <span style="color: #666;">项目数量:</span>
                        <span style="font-weight: bold;">${count}</span>
                        <span style="color: #999;">(${countPercent}%)</span>
                    </div>
                    <div style="margin-bottom: 4px;">
                        <span style="color: #666;">${distributionData.value_label}:</span>
                        <span style="font-weight: bold; color: #1890ff;">${value.toFixed(0)}</span>
                        <span style="color: #999;">(${valuePercent}%)</span>
                    </div>
                    <div style="margin-bottom: 4px;">
                        <span style="color: #666;">单项平均价值:</span>
                        <span style="font-weight: bold; color: #52c41a;">${avgValue.toFixed(0)}</span>
                    </div>
                    <div style="margin-top: 8px; color: #999; font-size: 12px;">
                        点击查看详细项目列表
                    </div>
                `;
            }
        },
        grid: {
            left: '15%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: categories,
            name: '分布区间',
            nameLocation: 'middle',
            nameGap: 30,
            axisLabel: {
                rotate: 0,
                interval: 0,
                fontSize: 11
            }
        },
        yAxis: {
            type: 'value',
            name: distributionData.value_label,
            nameLocation: 'middle',
            nameGap: 50,
            axisLabel: {
                formatter: function(value) {
                    return value >= 10000 ? (value/10000).toFixed(0) + '万' : value.toFixed(0);
                }
            }
        },
        series: [{
            type: 'bar',
            data: values,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#4facfe' },
                    { offset: 1, color: '#00f2fe' }
                ]),
                borderRadius: [4, 4, 0, 0]
            },
            label: {
                show: true,
                position: 'top',
                formatter: function(params) {
                    const dataIndex = params.dataIndex;
                    const count = counts[dataIndex];
                    const valuePercent = valuePercentages[dataIndex];
                    return `${count}项\n${valuePercent}%`;
                },
                fontSize: 10,
                color: '#666'
            },
            emphasis: {
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#667eea' },
                        { offset: 1, color: '#764ba2' }
                    ])
                }
            }
        }]
    };

    chart.setOption(option);

    // 添加点击事件实现下钻功能
    chart.on('click', function(params) {
        if (params.componentType === 'series') {
            const intervalName = params.name;
            showIntervalDetails(intervalName, distributionData);
        }
    });
}

// 显示区间详细信息的下钻功能
function showIntervalDetails(intervalName, distributionData) {
    const details = distributionData.interval_details[intervalName];
    if (!details || details.length === 0) {
        alert('该区间暂无详细数据');
        return;
    }

    // 创建模态框显示详细信息
    const modal = document.createElement('div');
    modal.className = 'interval-details-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
    `;

    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: white;
        border-radius: 8px;
        padding: 20px;
        max-width: 80%;
        max-height: 80%;
        overflow: auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    `;

    // 构建表格内容
    let tableHtml = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #333;">${intervalName} - 详细项目列表</h3>
            <button onclick="this.closest('.interval-details-modal').remove()"
                    style="background: #f5f5f5; border: none; border-radius: 4px; padding: 8px 12px; cursor: pointer;">
                关闭
            </button>
        </div>
        <div style="margin-bottom: 15px; color: #666;">
            共 ${details.length} 个项目，点击表头可排序
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: left;">项目名称</th>
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: right; cursor: pointer;"
                        onclick="sortIntervalTable(this, 'primary_value')">
                        ${distributionData.primary_label} ↕
                    </th>
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: right; cursor: pointer;"
                        onclick="sortIntervalTable(this, 'value')">
                        ${distributionData.value_label} ↕
                    </th>`;

    // 如果有毛利数据，添加毛利列
    if (details[0].profit !== undefined) {
        tableHtml += `
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: right; cursor: pointer;"
                        onclick="sortIntervalTable(this, 'profit')">
                        毛利(万元) ↕
                    </th>`;
    }

    tableHtml += `
                </tr>
            </thead>
            <tbody id="intervalDetailsTableBody">`;

    // 添加数据行
    details.forEach((item, index) => {
        const rowStyle = index % 2 === 0 ? 'background: #fff;' : 'background: #f8f9fa;';
        tableHtml += `
            <tr style="${rowStyle}">
                <td style="border: 1px solid #dee2e6; padding: 10px;">${item.name}</td>
                <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right;">${item.primary_value.toFixed(0)}</td>
                <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold; color: #1890ff;">${item.value.toFixed(0)}</td>`;

        if (item.profit !== undefined) {
            const profitColor = item.profit >= 0 ? '#52c41a' : '#ff4d4f';
            tableHtml += `
                <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; color: ${profitColor};">${item.profit.toFixed(0)}</td>`;
        }

        tableHtml += `</tr>`;
    });

    tableHtml += `
            </tbody>
        </table>
        <div style="margin-top: 15px; color: #999; font-size: 12px;">
            提示：点击表头可以按该列排序
        </div>
    `;

    modalContent.innerHTML = tableHtml;
    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    // 点击模态框外部关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// 区间详情表格排序功能
function sortIntervalTable(headerElement, sortField) {
    const table = headerElement.closest('table');
    const tbody = table.querySelector('#intervalDetailsTableBody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // 获取当前排序状态
    const isAscending = !headerElement.dataset.sortAsc || headerElement.dataset.sortAsc === 'false';

    // 重置所有表头的排序标识
    table.querySelectorAll('th').forEach(th => {
        th.innerHTML = th.innerHTML.replace(/[↑↓]/g, '↕');
        delete th.dataset.sortAsc;
    });

    // 设置当前表头的排序标识
    headerElement.dataset.sortAsc = isAscending;
    headerElement.innerHTML = headerElement.innerHTML.replace('↕', isAscending ? '↑' : '↓');

    // 排序数据
    rows.sort((a, b) => {
        let aValue, bValue;

        if (sortField === 'primary_value') {
            aValue = parseFloat(a.cells[1].textContent);
            bValue = parseFloat(b.cells[1].textContent);
        } else if (sortField === 'value') {
            aValue = parseFloat(a.cells[2].textContent);
            bValue = parseFloat(b.cells[2].textContent);
        } else if (sortField === 'profit') {
            aValue = parseFloat(a.cells[3].textContent);
            bValue = parseFloat(b.cells[3].textContent);
        }

        return isAscending ? aValue - bValue : bValue - aValue;
    });

    // 重新插入排序后的行
    rows.forEach(row => tbody.appendChild(row));
}

// 盈亏分析图
function displayProfitLossChart() {
    const profitLossData = analysisResult.additional_analysis.profit_loss_analysis;
    const chartContainer = document.getElementById('profitLossChart');

    const chart = echarts.init(chartContainer);
    chartInstances['profitLossChart'] = chart;

    const summary = profitLossData.summary;

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                if (params.name === '亏损项目') {
                    return `${params.name}: ${params.value} (${params.percent}%)<br/>
                            <span style="color: #666; font-size: 12px;">💡 点击查看亏损项目详情</span>`;
                } else if (params.name === '盈利项目') {
                    return `${params.name}: ${params.value} (${params.percent}%)<br/>
                            <span style="color: #666; font-size: 12px;">💡 点击查看盈利项目详情</span>`;
                }
                return `${params.name}: ${params.value} (${params.percent}%)`;
            }
        },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            data: [
                {
                    name: '盈利项目',
                    value: summary.profitable_count,
                    itemStyle: { color: '#4CAF50' }
                },
                {
                    name: '亏损项目',
                    value: summary.loss_count,
                    itemStyle: { color: '#F44336' }
                }
            ],
            label: {
                formatter: '{b}\n{c} ({d}%)'
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };

    chart.setOption(option);

    // 添加点击事件监听器
    chart.on('click', function(params) {
        if (params.name === '亏损项目') {
            // 触发亏损项目分析
            filterQuadrantByLossItems();
        } else if (params.name === '盈利项目') {
            // 触发盈利项目分析
            filterQuadrantByProfitableItems();
        }
    });
}

// 全局变量存储原始四象限数据
let originalQuadrantData = null;
let isQuadrantFiltered = false;
let currentFilterType = null; // 'loss' 或 'profitable'

// 根据亏损项目筛选四象限图
function filterQuadrantByLossItems() {
    if (!analysisResult || !analysisResult.additional_analysis.profit_loss_analysis) {
        showMessage('无法获取盈亏分析数据', 'error');
        return;
    }

    // 保存原始数据（如果还没有保存）
    if (!originalQuadrantData) {
        originalQuadrantData = JSON.parse(JSON.stringify(analysisResult.quadrant_analysis));
    }

    // 获取亏损项目数据
    const profitLossData = analysisResult.additional_analysis.profit_loss_analysis;
    const lossItems = profitLossData.loss_making_items;

    // 调试信息（亏损项目）
    console.log('亏损项目筛选调试信息:');
    console.log('- 亏损项目数量:', lossItems ? lossItems.length : 0);

    if (!lossItems || lossItems.length === 0) {
        showMessage('没有找到亏损项目', 'info');
        return;
    }

    // 获取分组字段名
    const groupField = getGroupFieldName();
    console.log('- 分组字段名:', groupField);

    // 创建亏损项目名称集合，用于快速查找
    const lossItemNames = new Set(lossItems.map(item => item[groupField]));
    console.log('- 亏损项目名称集合大小:', lossItemNames.size);

    // 筛选四象限数据，只保留亏损项目
    const filteredScatterData = originalQuadrantData.scatter_data.filter(item =>
        lossItemNames.has(item[groupField])
    );

    console.log('- 筛选后散点数据数量:', filteredScatterData.length);

    // 创建筛选后的四象限数据对象
    const filteredQuadrantData = {
        ...originalQuadrantData,
        scatter_data: filteredScatterData
    };

    // 更新全局分析结果中的四象限数据
    analysisResult.quadrant_analysis = filteredQuadrantData;

    // 标记为已筛选状态
    isQuadrantFiltered = true;
    currentFilterType = 'loss';

    // 重新渲染四象限图
    displayQuadrantAnalysis();

    // 显示筛选提示和重置按钮
    showFilterNotification();

    // 显示成功消息
    showMessage(`已筛选显示 ${filteredScatterData.length} 个亏损项目`, 'success');
}

// 根据盈利项目筛选四象限图
function filterQuadrantByProfitableItems() {
    console.log('=== 开始盈利项目筛选 ===');

    if (!analysisResult || !analysisResult.additional_analysis.profit_loss_analysis) {
        console.log('错误：无法获取盈亏分析数据');
        showMessage('无法获取盈亏分析数据', 'error');
        return;
    }

    // 保存原始数据（如果还没有保存）
    if (!originalQuadrantData) {
        originalQuadrantData = JSON.parse(JSON.stringify(analysisResult.quadrant_analysis));
        console.log('- 保存原始四象限数据，数据点数量:', originalQuadrantData.scatter_data.length);
    } else {
        console.log('- 使用已保存的原始数据，数据点数量:', originalQuadrantData.scatter_data.length);
    }

    // 获取盈利项目数据
    const profitLossData = analysisResult.additional_analysis.profit_loss_analysis;
    const profitableItems = profitLossData.profitable_items;

    // 调试信息
    console.log('盈利项目筛选调试信息:');
    console.log('- 盈利项目数量:', profitableItems ? profitableItems.length : 0);
    console.log('- 原始散点数据数量:', originalQuadrantData.scatter_data.length);

    if (!profitableItems || profitableItems.length === 0) {
        console.log('没有找到盈利项目');
        showMessage('没有找到盈利项目', 'info');
        return;
    }

    // 获取分组字段名
    const groupField = getGroupFieldName();
    console.log('- 分组字段名:', groupField);

    if (!groupField) {
        console.log('错误：分组字段名为空');
        showMessage('无法获取分组字段名', 'error');
        return;
    }

    // 增强调试：详细检查字段结构
    console.log('=== 字段结构详细分析 ===');
    
    // 检查盈利项目的所有字段
    if (profitableItems.length > 0) {
        console.log('盈利项目字段结构:');
        const profitableFields = Object.keys(profitableItems[0]);
        console.log('- 所有字段名:', profitableFields);
        console.log('- 字段数量:', profitableFields.length);
        console.log('- 前3个盈利项目示例:');
        profitableItems.slice(0, 3).forEach((item, index) => {
            console.log(`  项目${index + 1}:`, item);
        });
    }

    // 检查散点数据的所有字段
    if (originalQuadrantData.scatter_data.length > 0) {
        console.log('\n散点数据字段结构:');
        const scatterFields = Object.keys(originalQuadrantData.scatter_data[0]);
        console.log('- 所有字段名:', scatterFields);
        console.log('- 字段数量:', scatterFields.length);
        console.log('- 前3个散点数据示例:');
        originalQuadrantData.scatter_data.slice(0, 3).forEach((item, index) => {
            console.log(`  数据${index + 1}:`, item);
        });
    }

    // 创建灵活的字段映射函数
    function findMatchingField(data, targetFieldName, possibleFieldPatterns) {
        if (!data || typeof data !== 'object') return null;
        
        // 1. 首先尝试精确匹配
        if (data[targetFieldName] !== undefined) {
            return targetFieldName;
        }
        
        // 2. 尝试忽略大小写的匹配
        const fields = Object.keys(data);
        const caseInsensitiveMatch = fields.find(f => 
            f.toLowerCase() === targetFieldName.toLowerCase()
        );
        if (caseInsensitiveMatch) {
            return caseInsensitiveMatch;
        }
        
        // 3. 尝试使用模式匹配
        if (possibleFieldPatterns && possibleFieldPatterns.length > 0) {
            for (const pattern of possibleFieldPatterns) {
                const patternMatch = fields.find(f => 
                    f.toLowerCase().includes(pattern.toLowerCase()) &&
                    !f.includes('数量') && 
                    !f.includes('金额') && 
                    !f.includes('毛利') &&
                    !f.includes('成本') &&
                    !f.includes('占比') &&
                    !f.includes('率') &&
                    !f.includes('统计')
                );
                if (patternMatch) {
                    return patternMatch;
                }
            }
        }
        
        // 4. 检查是否有index字段
        if (data.index !== undefined) {
            return 'index';
        }
        
        return null;
    }
    
    // 根据分析类型定义可能的字段模式
    const fieldPatterns = {
        'product': ['产品', 'product', 'sku', '物料', '商品'],
        'customer': ['客户', 'customer', 'client', '买家'],
        'region': ['地区', 'region', '区域', '省份', 'area']
    };
    const possiblePatterns = fieldPatterns[currentAnalysisType] || [];
    
    // 在盈利项目中查找实际字段名
    let profitableFieldName = groupField;
    if (profitableItems.length > 0) {
        const detectedField = findMatchingField(profitableItems[0], groupField, possiblePatterns);
        if (detectedField && detectedField !== groupField) {
            console.log(`- 在盈利项目中找到匹配字段: '${detectedField}' (原始: '${groupField}')`);
            profitableFieldName = detectedField;
        }
    }
    
    // 在散点数据中查找实际字段名
    let scatterFieldName = groupField;
    if (originalQuadrantData.scatter_data.length > 0) {
        const detectedField = findMatchingField(originalQuadrantData.scatter_data[0], groupField, possiblePatterns);
        if (detectedField && detectedField !== groupField) {
            console.log(`- 在散点数据中找到匹配字段: '${detectedField}' (原始: '${groupField}')`);
            scatterFieldName = detectedField;
        }
    }

    // 创建盈利项目名称集合，使用检测到的字段名
    let profitableItemNames = new Set(profitableItems.map(item => {
        const name = item[profitableFieldName];
        if (name === undefined || name === null) {
            console.log(`警告：盈利项目中发现空名称 (字段: ${profitableFieldName}):`, item);
        }
        return name;
    }).filter(name => name !== undefined && name !== null));

    // 如果没有找到任何名称，尝试其他可能的字段名
    if (profitableItemNames.size === 0 && profitableItems.length > 0) {
        console.log('尝试使用其他字段名...');
        const firstItem = profitableItems[0];
        const possibleFields = Object.keys(firstItem);
        console.log('可用字段:', possibleFields);

        // 尝试找到包含名称的字段
        for (const field of possibleFields) {
            if (field.includes('名称') || field.includes('客户') || field.includes('产品') || field.includes('地区')) {
                console.log('尝试字段:', field);
                profitableItemNames = new Set(profitableItems.map(item => item[field]).filter(name => name !== undefined && name !== null));
                if (profitableItemNames.size > 0) {
                    console.log('找到匹配字段:', field);
                    break;
                }
            }
        }
    }

    console.log('- 盈利项目名称集合大小:', profitableItemNames.size);
    console.log('- 盈利项目名称示例:', Array.from(profitableItemNames).slice(0, 5));

    // 调试：检查散点数据中的名称，使用检测到的字段名
    const scatterItemNames = new Set(originalQuadrantData.scatter_data.map(item => {
        const name = item[scatterFieldName];
        if (name === undefined || name === null) {
            console.log(`警告：散点数据中发现空名称 (字段: ${scatterFieldName}):`, item);
        }
        return name;
    }).filter(name => name !== undefined && name !== null));

    console.log('- 散点数据名称集合大小:', scatterItemNames.size);
    console.log('- 散点数据名称示例:', Array.from(scatterItemNames).slice(0, 5));

    // 调试：检查名称匹配情况
    const matchingNames = Array.from(profitableItemNames).filter(name => scatterItemNames.has(name));
    console.log('- 匹配的名称数量:', matchingNames.length);
    console.log('- 匹配的名称示例:', matchingNames.slice(0, 5));
    
    // 创建一个模糊匹配函数
    function fuzzyMatch(name1, name2) {
        if (!name1 || !name2) return false;
        
        // 去除空格和特殊字符
        const clean1 = name1.toString().replace(/[\s\-_]/g, '').toLowerCase();
        const clean2 = name2.toString().replace(/[\s\-_]/g, '').toLowerCase();
        
        // 完全匹配
        if (clean1 === clean2) return true;
        
        // 包含关系
        if (clean1.includes(clean2) || clean2.includes(clean1)) return true;
        
        // 去除后缀后匹配（如 "ABC公司" 和 "ABC"）
        const suffix = ['公司', '有限公司', '股份有限公司', '集团', '厂', '店'];
        for (const s of suffix) {
            const cleaned1 = clean1.replace(new RegExp(s + '$'), '');
            const cleaned2 = clean2.replace(new RegExp(s + '$'), '');
            if (cleaned1 === cleaned2) return true;
        }
        
        return false;
    }
    
    // 如果没有匹配的名称，尝试模糊匹配
    if (matchingNames.length === 0 && profitableItemNames.size > 0 && scatterItemNames.size > 0) {
        console.log('\n警告：没有精确匹配的名称，尝试模糊匹配...');
        
        // 尝试模糊匹配
        const fuzzyMatchedNames = [];
        profitableItemNames.forEach(profitName => {
            scatterItemNames.forEach(scatterName => {
                if (fuzzyMatch(profitName, scatterName)) {
                    fuzzyMatchedNames.push({ profitName, scatterName });
                }
            });
        });
        
        console.log('- 模糊匹配结果数量:', fuzzyMatchedNames.length);
        if (fuzzyMatchedNames.length > 0) {
            console.log('- 模糊匹配示例:', fuzzyMatchedNames.slice(0, 5));
        }
    }

    // 筛选四象限数据，只保留盈利项目，使用检测到的字段名
    const filteredScatterData = originalQuadrantData.scatter_data.filter(item => {
        const itemName = item[scatterFieldName];
        
        // 首先尝试精确匹配
        if (profitableItemNames.has(itemName)) {
            return true;
        }
        
        // 如果没有精确匹配，尝试模糊匹配
        for (const profitName of profitableItemNames) {
            if (fuzzyMatch && fuzzyMatch(itemName, profitName)) {
                return true;
            }
        }
        
        return false;
    });

    console.log('- 筛选后散点数据数量:', filteredScatterData.length);

    // 创建筛选后的四象限数据对象
    const filteredQuadrantData = {
        ...originalQuadrantData,
        scatter_data: filteredScatterData
    };

    console.log('- 筛选后的四象限数据对象:', filteredQuadrantData);

    // 更新全局分析结果中的四象限数据
    analysisResult.quadrant_analysis = filteredQuadrantData;

    // 标记为已筛选状态
    isQuadrantFiltered = true;
    currentFilterType = 'profitable';

    console.log('- 开始重新渲染四象限图...');
    console.log('- 更新前的四象限数据点数量:', analysisResult.quadrant_analysis.scatter_data.length);

    // 重新渲染四象限图
    displayQuadrantAnalysis();

    console.log('- 四象限图渲染完成');
    console.log('- 更新后的四象限数据点数量:', analysisResult.quadrant_analysis.scatter_data.length);

    // 显示筛选提示和重置按钮
    showFilterNotification();

    // 显示成功消息
    showMessage(`已筛选显示 ${filteredScatterData.length} 个盈利项目`, 'success');

    console.log('=== 盈利项目筛选完成 ===');
}

// 重置四象限图到全部数据
function resetQuadrantFilter() {
    if (!originalQuadrantData) {
        return;
    }

    // 恢复原始数据
    analysisResult.quadrant_analysis = JSON.parse(JSON.stringify(originalQuadrantData));

    // 重新渲染四象限图
    displayQuadrantAnalysis();

    // 标记为未筛选状态
    isQuadrantFiltered = false;
    currentFilterType = null;

    // 隐藏筛选提示
    hideFilterNotification();

    showMessage('已重置为显示全部数据', 'success');
}

// 显示筛选通知
function showFilterNotification() {
    // 根据筛选类型确定显示文本和样式
    const filterConfig = {
        'loss': {
            text: '当前显示：仅亏损项目',
            icon: '🔍',
            bgClass: 'filter-notification-loss'
        },
        'profitable': {
            text: '当前显示：仅盈利项目',
            icon: '💰',
            bgClass: 'filter-notification-profitable'
        }
    };

    const config = filterConfig[currentFilterType] || filterConfig['loss'];

    // 检查是否已存在通知
    let notification = document.getElementById('quadrant-filter-notification');

    if (!notification) {
        // 创建通知元素
        notification = document.createElement('div');
        notification.id = 'quadrant-filter-notification';
        notification.className = 'filter-notification';

        // 将通知插入到四象限图容器上方
        const quadrantContainer = document.getElementById('quadrantChart').parentElement;
        quadrantContainer.insertBefore(notification, document.getElementById('quadrantChart'));
    }

    // 更新通知内容和样式
    notification.className = `filter-notification ${config.bgClass}`;
    notification.innerHTML = `
        <div class="filter-notification-content">
            <span class="filter-icon">${config.icon}</span>
            <span class="filter-text">${config.text}</span>
            <button class="reset-filter-btn" onclick="resetQuadrantFilter()">
                <span>↻</span> 显示全部
            </button>
        </div>
    `;

    // 显示通知（添加动画效果）
    notification.style.display = 'block';
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
}

// 隐藏筛选通知
function hideFilterNotification() {
    const notification = document.getElementById('quadrant-filter-notification');
    if (notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.style.display = 'none';
        }, 300);
    }
}

// 贡献度分析图
function displayContributionChart() {
    const contributionData = analysisResult.additional_analysis.contribution_analysis;
    const chartContainer = document.getElementById('contributionChart');

    const chart = echarts.init(chartContainer);
    chartInstances['contributionChart'] = chart;

    // 选择第一个可用的字段进行展示
    const firstField = Object.keys(contributionData)[0];
    if (!firstField) return;

    const data = contributionData[firstField].top_contributors.slice(0, 10);
    const categories = data.map(item => item[getGroupFieldName()]);
    const values = data.map(item => item[`${firstField}_contribution`]);

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        xAxis: {
            type: 'category',
            data: categories,
            axisLabel: {
                rotate: 45,
                interval: 0
            }
        },
        yAxis: {
            type: 'value',
            name: '贡献度(%)'
        },
        series: [{
            type: 'bar',
            data: values,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#667eea' },
                    { offset: 1, color: '#764ba2' }
                ])
            }
        }]
    };

    chart.setOption(option);
}

// 显示数据表格
function displayDataTable() {
    const tableData = analysisResult.aggregated_data;
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');

    if (!tableData || tableData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="100%">暂无数据</td></tr>';
        return;
    }

    // 定义字段显示顺序和格式化规则
    const fieldConfig = getTableFieldConfig();

    // 生成表头
    let headerHtml = '<tr>';
    fieldConfig.forEach(config => {
        if (tableData[0].hasOwnProperty(config.key)) {
            const sortable = config.format === 'number' || config.format === 'integer' || config.format === 'currency' || config.format === 'percent';
            const sortIcon = sortable ? '<i class="fas fa-sort sort-icon"></i>' : '';
            const clickHandler = sortable ? `onclick="sortTable('${config.key}')"` : '';
            const cursorStyle = sortable ? 'cursor: pointer;' : '';

            headerHtml += `<th class="${config.className || ''}" style="${config.headerStyle || ''}${cursorStyle}" ${clickHandler}>
                ${config.label}${sortIcon}
            </th>`;
        }
    });
    headerHtml += '</tr>';
    tableHeader.innerHTML = headerHtml;

    // 生成表格数据
    displayTableData(tableData, fieldConfig);

    // 设置搜索和筛选
    setupTableControls(tableData);
}

// 获取表格字段配置
function getTableFieldConfig() {
    const baseConfig = [
        { key: getGroupFieldName(), label: getGroupFieldLabel(), className: 'col-name', headerStyle: 'min-width: 150px;' },
        { key: '象限名称', label: '象限分类', className: 'col-quadrant', headerStyle: 'min-width: 100px;' },
    ];

    // 根据分析类型添加特定字段
    if (currentAnalysisType === 'product') {
        baseConfig.push(
            { key: '销量(吨)', label: '销量(吨)', className: 'col-number', headerStyle: 'min-width: 80px;', format: 'number' },
            { key: '吨毛利', label: '吨毛利(元)', className: 'col-number', headerStyle: 'min-width: 100px;', format: 'currency' },
            { key: '总金额(万元)', label: '总金额(万元)', className: 'col-number', headerStyle: 'min-width: 100px;', format: 'number' },
            { key: '总毛利(万元)', label: '总毛利(万元)', className: 'col-number', headerStyle: 'min-width: 100px;', format: 'number' }
        );
    } else if (currentAnalysisType === 'customer') {
        baseConfig.push(
            { key: '采购金额(万元)', label: '采购金额(万元)', className: 'col-number', headerStyle: 'min-width: 120px;', format: 'number' },
            { key: '毛利贡献(万元)', label: '毛利贡献(万元)', className: 'col-number', headerStyle: 'min-width: 120px;', format: 'number' },
            { key: '采购数量(吨)', label: '采购数量(吨)', className: 'col-number', headerStyle: 'min-width: 100px;', format: 'number' },
            { key: '客户毛利率', label: '毛利率(%)', className: 'col-number', headerStyle: 'min-width: 80px;', format: 'percent' }
        );
    } else if (currentAnalysisType === 'region') {
        baseConfig.push(
            { key: '地区销售金额(万元)', label: '销售金额(万元)', className: 'col-number', headerStyle: 'min-width: 120px;', format: 'number' },
            { key: '地区毛利贡献(万元)', label: '毛利贡献(万元)', className: 'col-number', headerStyle: 'min-width: 120px;', format: 'number' },
            { key: '地区销售数量(吨)', label: '销售数量(吨)', className: 'col-number', headerStyle: 'min-width: 100px;', format: 'number' },
            { key: '地区客户数量', label: '客户数量', className: 'col-number', headerStyle: 'min-width: 80px;', format: 'integer' }
        );
    }

    // 添加成本相关字段（如果存在）
    const costFields = [
        { key: '总成本(万元)', label: '总成本(万元)', className: 'col-number', headerStyle: 'min-width: 100px;', format: 'number' },
        { key: '成本率', label: '成本率(%)', className: 'col-number', headerStyle: 'min-width: 80px;', format: 'percent' }
    ];

    costFields.forEach(field => {
        if (analysisResult.aggregated_data && analysisResult.aggregated_data[0] && analysisResult.aggregated_data[0].hasOwnProperty(field.key)) {
            baseConfig.push(field);
        }
    });

    // 添加策略建议
    baseConfig.push({ key: '建议策略', label: '建议策略', className: 'col-strategy', headerStyle: 'min-width: 200px;' });

    return baseConfig;
}

// 显示表格数据
function displayTableData(data, fieldConfig) {
    const tableBody = document.getElementById('tableBody');

    let bodyHtml = '';
    data.forEach(row => {
        bodyHtml += '<tr>';
        fieldConfig.forEach(config => {
            if (row.hasOwnProperty(config.key)) {
                const value = row[config.key];
                let displayValue = formatTableValue(value, config.format);
                let cellClass = config.className || '';

                // 为象限名称添加颜色样式
                if (config.key === '象限名称') {
                    const quadrantClass = getQuadrantClass(value);
                    cellClass += ` ${quadrantClass}`;
                }

                bodyHtml += `<td class="${cellClass}">${displayValue || ''}</td>`;
            }
        });
        bodyHtml += '</tr>';
    });

    tableBody.innerHTML = bodyHtml;
}

// 获取象限样式类
function getQuadrantClass(quadrantName) {
    const classMap = {
        '明星产品': 'quadrant-star',
        '金牛产品': 'quadrant-cash',
        '潜力产品': 'quadrant-potential',
        '瘦狗产品': 'quadrant-dog',
        '核心客户': 'quadrant-star',
        '增利客户': 'quadrant-cash',
        '成长客户': 'quadrant-potential',
        '机会客户': 'quadrant-dog',
        '核心市场': 'quadrant-star',
        '规模市场': 'quadrant-cash',
        '机会市场': 'quadrant-potential',
        '边缘市场': 'quadrant-dog'
    };
    return classMap[quadrantName] || '';
}

// 表格排序功能
let currentSortField = null;
let currentSortDirection = 'asc';

function sortTable(fieldKey) {
    const tableData = analysisResult.aggregated_data;
    const fieldConfig = getTableFieldConfig();

    // 切换排序方向
    if (currentSortField === fieldKey) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortField = fieldKey;
        currentSortDirection = 'desc'; // 数值字段默认降序
    }

    // 排序数据
    const sortedData = [...tableData].sort((a, b) => {
        let valueA = a[fieldKey];
        let valueB = b[fieldKey];

        // 处理数值类型
        if (typeof valueA === 'number' && typeof valueB === 'number') {
            return currentSortDirection === 'asc' ? valueA - valueB : valueB - valueA;
        }

        // 处理字符串类型
        valueA = String(valueA || '').toLowerCase();
        valueB = String(valueB || '').toLowerCase();

        if (currentSortDirection === 'asc') {
            return valueA.localeCompare(valueB);
        } else {
            return valueB.localeCompare(valueA);
        }
    });

    // 更新表头排序图标
    updateSortIcons(fieldKey, currentSortDirection);

    // 重新显示数据
    displayTableData(sortedData, fieldConfig);
}

function updateSortIcons(activeField, direction) {
    const sortIcons = document.querySelectorAll('.sort-icon');
    sortIcons.forEach(icon => {
        icon.className = 'fas fa-sort sort-icon';
    });

    // 更新当前排序字段的图标
    const activeHeader = document.querySelector(`th[onclick="sortTable('${activeField}')"] .sort-icon`);
    if (activeHeader) {
        activeHeader.className = direction === 'asc' ?
            'fas fa-sort-up sort-icon active' :
            'fas fa-sort-down sort-icon active';
    }
}

// 格式化表格值
function formatTableValue(value, format) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }

    switch (format) {
        case 'number':
            return typeof value === 'number' ?
                value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value;
        case 'integer':
            return typeof value === 'number' ?
                Math.round(value).toLocaleString() : value;
        case 'currency':
            return typeof value === 'number' ?
                value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : value;
        case 'percent':
            return typeof value === 'number' ?
                (value * 100).toFixed(2) + '%' : value;
        default:
            return value;
    }
}

// 设置表格控件
function setupTableControls(originalData) {
    const searchInput = document.getElementById('searchInput');
    const filterSelect = document.getElementById('filterSelect');
    const fieldConfig = getTableFieldConfig();

    // 搜索功能
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const filteredData = originalData.filter(row => {
            return Object.values(row).some(value =>
                String(value).toLowerCase().includes(searchTerm)
            );
        });
        displayTableData(filteredData, fieldConfig);
    });

    // 筛选功能（按象限）
    if (analysisResult.quadrant_analysis) {
        const quadrants = ['', '明星产品', '金牛产品', '潜力产品', '瘦狗产品'];
        const quadrantNames = {
            'product': quadrants,
            'customer': ['', '核心客户', '增利客户', '成长客户', '机会客户'],
            'region': ['', '核心市场', '规模市场', '机会市场', '边缘市场']
        };

        const options = quadrantNames[currentAnalysisType] || quadrants;
        filterSelect.innerHTML = options.map(option =>
            `<option value="${option}">${option || '全部'}</option>`
        ).join('');

        filterSelect.addEventListener('change', function() {
            const filterValue = this.value;
            if (!filterValue) {
                displayTableData(originalData, fieldConfig);
                return;
            }

            const filteredData = originalData.filter(row =>
                row.象限名称 === filterValue
            );
            displayTableData(filteredData, fieldConfig);
        });
    }
}

// 根据项目筛选表格
function filterTableByItem(item) {
    const groupField = getGroupFieldName();
    const itemName = item[groupField];

    const searchInput = document.getElementById('searchInput');
    searchInput.value = itemName;

    const filteredData = analysisResult.aggregated_data.filter(row =>
        row[groupField] === itemName
    );
    const fieldConfig = getTableFieldConfig();
    displayTableData(filteredData, fieldConfig);
}

// 导出报告
async function handleExportReport() {
    if (!currentFileId) {
        showMessage('没有可导出的分析结果', 'error');
        return;
    }

    showLoading('生成报告中...');

    try {
        const response = await fetch('/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `分析报告_${new Date().toISOString().slice(0, 10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showMessage('报告导出成功', 'success');
        } else {
            const result = await response.json();
            throw new Error(result.error);
        }
    } catch (error) {
        showMessage('导出失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// 新建分析
function handleNewAnalysis() {
    // 重置所有状态
    currentFileId = null;
    currentSheetName = null;
    currentAnalysisType = null;
    analysisResult = null;

    // 隐藏所有区域
    sheetSection.style.display = 'none';
    fieldSection.style.display = 'none';
    unitSection.style.display = 'none';
    analysisSection.style.display = 'none';
    uploadProgress.style.display = 'none';

    // 重置表单
    fileInput.value = '';
    document.querySelectorAll('input[name="analysisType"]').forEach(radio => {
        radio.checked = false;
    });

    // 重置按钮状态
    document.getElementById('nextToFieldDetection').disabled = true;
    document.getElementById('nextToUnitConfirmation').disabled = true;
    document.getElementById('startAnalysis').disabled = true;

    showMessage('已重置，可以开始新的分析', 'success');
}

// 显示加载状态
function showLoading(text = '处理中...') {
    loadingText.textContent = text;
    loadingOverlay.style.display = 'flex';
}

// 隐藏加载状态
function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// 显示消息
function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <i class="fas fa-${getMessageIcon(type)}"></i>
        ${message}
    `;

    messageContainer.appendChild(messageDiv);

    // 3秒后自动移除
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 3000);
}

// 获取消息图标
function getMessageIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 响应式图表处理
function resizeCharts() {
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

// 窗口大小变化时重新调整图表大小
window.addEventListener('resize', function() {
    clearTimeout(window.resizeTimeout);
    window.resizeTimeout = setTimeout(resizeCharts, 100);
});

// 显示成本分析图表
function displayCostAnalysisCharts() {
    const costAnalysis = analysisResult.additional_analysis.cost_analysis;

    // 1. 成本构成饼图
    if (costAnalysis.composition) {
        displayCostCompositionChart(costAnalysis.composition);
    }

    // 2. 成本率分布图
    if (costAnalysis.rate_distribution) {
        displayCostRateChart(costAnalysis.rate_distribution);
    }

    // 3. 成本效率散点图
    if (costAnalysis.efficiency && !costAnalysis.efficiency.error) {
        displayCostEfficiencyChart(costAnalysis.efficiency);
    }
}

// 成本构成饼图
function displayCostCompositionChart(compositionData) {
    const chartContainer = document.getElementById('costCompositionChart');
    const chart = echarts.init(chartContainer);
    chartInstances['costCompositionChart'] = chart;

    const data = compositionData.composition_data.map(item => ({
        name: item.name,
        value: item.value
    }));

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c}万元 ({d}%)'
        },
        series: [{
            type: 'pie',
            radius: '60%',
            data: data,
            itemStyle: {
                borderRadius: 5,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: {
                formatter: '{b}\n{d}%'
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };

    chart.setOption(option);
}

// 成本率分布图
function displayCostRateChart(rateData) {
    const chartContainer = document.getElementById('costRateChart');
    const chart = echarts.init(chartContainer);
    chartInstances['costRateChart'] = chart;

    const categories = rateData.distribution_data.map(item => item.interval);
    const values = rateData.distribution_data.map(item => item.count);

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                const data = rateData.distribution_data[params[0].dataIndex];
                return `${params[0].name}<br/>数量: ${data.count}<br/>占比: ${data.percentage}%`;
            }
        },
        xAxis: {
            type: 'category',
            data: categories,
            name: '成本率区间'
        },
        yAxis: {
            type: 'value',
            name: '数量'
        },
        series: [{
            type: 'bar',
            data: values,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#ffc107' },
                    { offset: 1, color: '#fd7e14' }
                ])
            }
        }]
    };

    chart.setOption(option);
}

// 成本效率散点图
function displayCostEfficiencyChart(efficiencyData) {
    const chartContainer = document.getElementById('costEfficiencyChart');
    const chart = echarts.init(chartContainer);
    chartInstances['costEfficiencyChart'] = chart;

    const scatterData = efficiencyData.scatter_data.map(item => [
        item.cost_rate,
        item.efficiency_value,
        item
    ]);

    const option = {
        title: {
            text: '成本效率分析',
            left: 'center',
            textStyle: {
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                const data = params.data[2];
                return `${data.name}<br/>
                        成本率: ${(data.cost_rate * 100).toFixed(2)}%<br/>
                        ${efficiencyData.y_label}: ${data.efficiency_value.toFixed(2)}<br/>
                        分类: ${getCostEfficiencyLabel(data.quadrant)}`;
            }
        },
        xAxis: {
            type: 'value',
            name: efficiencyData.x_label,
            nameLocation: 'middle',
            nameGap: 30,
            axisLabel: {
                formatter: function(value) {
                    return (value * 100).toFixed(0) + '%';
                }
            }
        },
        yAxis: {
            type: 'value',
            name: efficiencyData.y_label,
            nameLocation: 'middle',
            nameGap: 50
        },
        series: [{
            type: 'scatter',
            data: scatterData,
            symbolSize: 8,
            itemStyle: {
                color: function(params) {
                    const quadrant = params.data[2].quadrant;
                    const colors = {
                        'efficient': '#4CAF50',    // 绿色 - 高效
                        'low_volume': '#2196F3',   // 蓝色 - 低量
                        'high_cost': '#FF9800',    // 橙色 - 高成本
                        'inefficient': '#F44336'   // 红色 - 低效
                    };
                    return colors[quadrant] || '#666';
                }
            },
            markLine: {
                silent: true,
                symbol: 'none',
                lineStyle: {
                    color: '#999',
                    type: 'dashed',
                    width: 1
                },
                data: [
                    {
                        xAxis: efficiencyData.avg_cost_rate,
                        name: '平均成本率'
                    },
                    {
                        yAxis: efficiencyData.avg_efficiency,
                        name: '平均效率'
                    }
                ]
            }
        }]
    };

    chart.setOption(option);
}

// 获取成本效率分类标签
function getCostEfficiencyLabel(quadrant) {
    const labels = {
        'efficient': '高效率低成本',
        'low_volume': '低效率低成本',
        'high_cost': '高效率高成本',
        'inefficient': '低效率高成本'
    };
    return labels[quadrant] || '未分类';
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 确保图表容器有正确的尺寸
    setTimeout(resizeCharts, 500);
});
