// 修复表格显示问题的脚本

console.log('=== 开始修复表格显示问题 ===');

// 修复后的 displayDataTable 函数
function fixedDisplayDataTable() {
    console.log('执行修复后的 displayDataTable 函数');
    
    if (!analysisResult) {
        console.error('没有分析结果');
        return;
    }
    
    const tableData = analysisResult.aggregated_data;
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');
    
    if (!tableData || tableData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="100%">暂无数据</td></tr>';
        return;
    }

    console.log('表格数据行数:', tableData.length);
    console.log('示例数据:', tableData[0]);

    // 获取产品字段名
    let productFieldName = null;
    if (analysisResult.field_detection && analysisResult.field_detection.detected_fields) {
        productFieldName = analysisResult.field_detection.detected_fields.product;
    }
    
    // 如果没有找到产品字段，尝试从数据中查找
    if (!productFieldName && tableData.length > 0) {
        const sampleData = tableData[0];
        const possibleFields = Object.keys(sampleData);
        
        // 查找包含产品相关关键词的字段
        const productKeywords = ['产品', 'product', 'sku', '物料', '商品', '名称'];
        for (const keyword of productKeywords) {
            const matchedField = possibleFields.find(field => 
                field.toLowerCase().includes(keyword.toLowerCase()) &&
                !field.includes('数量') && 
                !field.includes('金额') && 
                !field.includes('毛利') &&
                !field.includes('成本') &&
                !field.includes('象限')
            );
            if (matchedField) {
                productFieldName = matchedField;
                break;
            }
        }
    }
    
    console.log('找到的产品字段名:', productFieldName);

    // 定义要显示的列
    const columns = [
        { key: productFieldName, label: '产品名称', type: 'text' },
        { key: '象限名称', label: '象限分类', type: 'text' },
        { key: '销量(吨)', label: '销量(吨)', type: 'number' },
        { key: '总金额(万元)', label: '总金额(万元)', type: 'number' },
        { key: '总毛利(万元)', label: '总毛利(万元)', type: 'profit' },
        { key: '吨毛利', label: '吨毛利(元)', type: 'profit' }
    ];

    // 过滤出实际存在的列
    const availableColumns = columns.filter(col => {
        if (!col.key) return false;
        return tableData[0].hasOwnProperty(col.key);
    });

    console.log('可用列:', availableColumns.map(c => c.key));

    // 生成表头
    let headerHtml = '<tr>';
    availableColumns.forEach(col => {
        headerHtml += `<th>${col.label}</th>`;
    });
    headerHtml += '</tr>';
    tableHeader.innerHTML = headerHtml;

    // 生成表格数据
    let bodyHtml = '';
    tableData.forEach((row, index) => {
        bodyHtml += '<tr>';
        availableColumns.forEach(col => {
            const value = row[col.key];
            let displayValue = value;
            let cellClass = '';
            
            // 格式化数值
            if (typeof value === 'number') {
                if (col.type === 'profit') {
                    displayValue = Math.round(value);
                    cellClass = value >= 0 ? 'profit-positive' : 'profit-negative';
                } else if (col.type === 'number') {
                    displayValue = value.toFixed(2);
                }
            }
            
            // 象限标签特殊处理
            if (col.key === '象限名称') {
                const quadrantClass = getQuadrantClass(value);
                displayValue = `<span class="quadrant-badge ${quadrantClass}">${value}</span>`;
            }
            
            bodyHtml += `<td class="${cellClass}">${displayValue || ''}</td>`;
        });
        bodyHtml += '</tr>';
    });
    
    tableBody.innerHTML = bodyHtml;
    
    console.log('✓ 表格修复完成');
}

// 象限样式类映射
function getQuadrantClass(quadrantName) {
    const classMap = {
        '明星产品': 'quadrant-star',
        '金牛产品': 'quadrant-cash',
        '潜力产品': 'quadrant-potential',
        '瘦狗产品': 'quadrant-dog'
    };
    return classMap[quadrantName] || '';
}

// 简化的列设置功能
function initializeSimpleColumnSettings() {
    console.log('初始化简化列设置功能');
    
    const columnSettingsBtn = document.getElementById('columnSettingsBtn');
    const columnSettingsMenu = document.getElementById('columnSettingsMenu');
    
    if (!columnSettingsBtn || !columnSettingsMenu) {
        console.warn('列设置元素不存在');
        return;
    }
    
    // 绑定按钮点击事件
    columnSettingsBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        
        if (columnSettingsMenu.style.display === 'block') {
            columnSettingsMenu.style.display = 'none';
        } else {
            columnSettingsMenu.style.display = 'block';
            generateSimpleColumnOptions();
        }
    });
    
    // 点击其他地方关闭菜单
    document.addEventListener('click', function(e) {
        if (!columnSettingsMenu.contains(e.target) && !columnSettingsBtn.contains(e.target)) {
            columnSettingsMenu.style.display = 'none';
        }
    });
}

// 生成简化的列选项
function generateSimpleColumnOptions() {
    const columnList = document.querySelector('#columnSettingsMenu .column-list');
    if (!columnList) return;
    
    const columns = [
        { key: 'product', label: '产品名称', required: true },
        { key: 'quadrant', label: '象限分类', required: true },
        { key: 'quantity', label: '销量(吨)', required: false },
        { key: 'amount', label: '总金额(万元)', required: false },
        { key: 'profit', label: '总毛利(万元)', required: false },
        { key: 'ton_profit', label: '吨毛利(元)', required: false }
    ];
    
    let optionsHtml = '';
    
    columns.forEach(col => {
        const checked = col.required ? 'checked disabled' : 'checked';
        const note = col.required ? '<small class="column-note">必显</small>' : '';
        
        optionsHtml += `
            <label class="column-option ${col.required ? 'basic-column' : ''}">
                <input type="checkbox" value="${col.key}" ${checked} 
                       onchange="handleSimpleColumnToggle('${col.key}', this.checked)">
                <span class="column-label">${col.label}</span>
                ${note}
            </label>
        `;
    });
    
    columnList.innerHTML = optionsHtml;
}

// 处理列切换
function handleSimpleColumnToggle(columnKey, isVisible) {
    console.log(`列切换: ${columnKey} = ${isVisible}`);
    
    // 这里可以添加列显示/隐藏的逻辑
    // 为了简化，暂时只重新渲染表格
    setTimeout(() => {
        fixedDisplayDataTable();
    }, 100);
}

// 替换原有的 displayDataTable 函数
if (typeof displayDataTable !== 'undefined') {
    console.log('替换原有的 displayDataTable 函数');
    window.originalDisplayDataTable = displayDataTable;
    window.displayDataTable = fixedDisplayDataTable;
}

// 初始化修复
console.log('开始初始化修复...');
initializeSimpleColumnSettings();

// 如果有分析结果，立即修复表格
if (typeof analysisResult !== 'undefined' && analysisResult) {
    console.log('发现分析结果，立即修复表格');
    fixedDisplayDataTable();
}

console.log('=== 修复脚本加载完成 ===');