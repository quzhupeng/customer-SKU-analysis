// 全局变量
let currentFileId = null;
let currentSheetName = null;
let currentAnalysisType = null;
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
    
    showLoading('分析数据中，请稍候...');
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet_name: currentSheetName,
                analysis_type: currentAnalysisType,
                unit_confirmations: unitConfirmations
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            analysisResult = result.data;
            displayAnalysisResults();
            analysisSection.style.display = 'block';
            hideLoading();
            showMessage('分析完成', 'success');
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        hideLoading();
        showMessage('分析失败: ' + error.message, 'error');
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
                return `${getGroupFieldName()}: ${data[getGroupFieldName()]}<br/>
                        ${quadrantData.x_label}: ${params.data[0]}<br/>
                        ${quadrantData.y_label}: ${params.data[1]}<br/>
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
                        1: '#4CAF50',  // 绿色 - 明星
                        2: '#FF9800',  // 橙色 - 金牛
                        3: '#2196F3',  // 蓝色 - 潜力
                        4: '#F44336'   // 红色 - 瘦狗
                    };
                    return colors[quadrant] || '#666';
                }
            }
        }],
        // 添加分割线
        graphic: [
            {
                type: 'line',
                shape: {
                    x1: quadrantData.x_avg,
                    y1: 0,
                    x2: quadrantData.x_avg,
                    y2: '100%'
                },
                style: {
                    stroke: '#999',
                    lineDash: [5, 5]
                }
            },
            {
                type: 'line',
                shape: {
                    x1: 0,
                    y1: quadrantData.y_avg,
                    x2: '100%',
                    y2: quadrantData.y_avg
                },
                style: {
                    stroke: '#999',
                    lineDash: [5, 5]
                }
            }
        ]
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

// 显示策略卡片
function displayStrategyCards() {
    const quadrantStats = analysisResult.quadrant_analysis.quadrant_stats;
    const cardsContainer = document.getElementById('strategyCards');

    let html = '';

    [1, 2, 3, 4].forEach(quadrant => {
        const stats = quadrantStats[quadrant];
        const colors = {
            1: '#4CAF50',  // 绿色
            2: '#FF9800',  // 橙色
            3: '#2196F3',  // 蓝色
            4: '#F44336'   // 红色
        };

        html += `
            <div class="strategy-card" style="border-left-color: ${colors[quadrant]}">
                <h4>${stats.name}</h4>
                <div class="description">${stats.description}</div>
                <div class="count">数量: ${stats.count}</div>
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

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
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

// 分布图
function displayDistributionChart() {
    const distributionData = analysisResult.additional_analysis.distribution_analysis;
    const chartContainer = document.getElementById('distributionChart');

    const chart = echarts.init(chartContainer);
    chartInstances['distributionChart'] = chart;

    const data = distributionData.interval_data;
    const categories = data.map(item => item.区间);
    const values = data.map(item => item.数量);

    const option = {
        title: {
            text: distributionData.title,
            left: 'center',
            textStyle: {
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        series: [{
            type: 'pie',
            radius: '60%',
            data: categories.map((cat, index) => ({
                name: cat,
                value: values[index]
            })),
            itemStyle: {
                borderRadius: 5,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: {
                show: true,
                formatter: '{b}\n{c}'
            }
        }]
    };

    chart.setOption(option);
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

    // 生成表头
    const columns = Object.keys(tableData[0]);
    let headerHtml = '<tr>';
    columns.forEach(column => {
        headerHtml += `<th>${column}</th>`;
    });
    headerHtml += '</tr>';
    tableHeader.innerHTML = headerHtml;

    // 生成表格数据
    displayTableData(tableData);

    // 设置搜索和筛选
    setupTableControls(tableData);
}

// 显示表格数据
function displayTableData(data) {
    const tableBody = document.getElementById('tableBody');

    let bodyHtml = '';
    data.forEach(row => {
        bodyHtml += '<tr>';
        Object.values(row).forEach(value => {
            const displayValue = typeof value === 'number' ?
                value.toLocaleString(undefined, { maximumFractionDigits: 2 }) :
                value;
            bodyHtml += `<td>${displayValue || ''}</td>`;
        });
        bodyHtml += '</tr>';
    });

    tableBody.innerHTML = bodyHtml;
}

// 设置表格控件
function setupTableControls(originalData) {
    const searchInput = document.getElementById('searchInput');
    const filterSelect = document.getElementById('filterSelect');

    // 搜索功能
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const filteredData = originalData.filter(row => {
            return Object.values(row).some(value =>
                String(value).toLowerCase().includes(searchTerm)
            );
        });
        displayTableData(filteredData);
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
                displayTableData(originalData);
                return;
            }

            const filteredData = originalData.filter(row =>
                row.象限名称 === filterValue
            );
            displayTableData(filteredData);
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

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 确保图表容器有正确的尺寸
    setTimeout(resizeCharts, 500);
});
