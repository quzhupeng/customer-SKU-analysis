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
    
    const chart = echarts.init(chartContainer);
    chartInstances['quadrantChart'] = chart;
    
    // 准备散点数据
    const scatterData = quadrantData.scatter_data.map(item => {
        const xField = getXFieldName();
        const yField = getYFieldName();
        return [item[xField], item[yField], item];
    });
    
    const option = {
        title: {
            text: '四象限分析',
            left: 'center'
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
    
    chart.setOption(option);
    
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
    const fieldMap = {
        'product': analysisResult.field_detection.detected_fields.product,
        'customer': analysisResult.field_detection.detected_fields.customer,
        'region': analysisResult.field_detection.detected_fields.region
    };
    return fieldMap[currentAnalysisType];
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
            trigger: 'item'
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
            }
        }]
    };

    chart.setOption(option);
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
    displayTableData(filteredData);
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
