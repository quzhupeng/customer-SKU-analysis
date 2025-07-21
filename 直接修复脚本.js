// 直接修复脚本 - 在浏览器控制台中运行

console.log('🔧 开始修复明细数据表格...');

// 1. 诊断当前状态
function diagnoseTableIssue() {
    console.log('📊 诊断当前状态:');
    console.log('- 分析类型:', currentAnalysisType);
    console.log('- 分析结果存在:', !!analysisResult);
    
    if (!analysisResult || !analysisResult.aggregated_data) {
        console.error('❌ 没有分析数据，请先执行分析');
        return false;
    }
    
    const data = analysisResult.aggregated_data;
    console.log('- 数据行数:', data.length);
    
    if (data.length > 0) {
        const sample = data[0];
        const fields = Object.keys(sample);
        console.log('- 可用字段:', fields);
        
        // 查找产品字段
        const productFields = fields.filter(field => 
            field.includes('物料') || field.includes('产品') || 
            field.includes('名称') && !field.includes('象限')
        );
        console.log('- 产品相关字段:', productFields);
        
        return { data, fields, productFields };
    }
    
    return false;
}

// 2. 修复表格显示
function fixTableDisplay() {
    const diagnosis = diagnoseTableIssue();
    if (!diagnosis) return;
    
    const { data, fields, productFields } = diagnosis;
    
    // 确定产品字段
    let productField = null;
    if (productFields.length > 0) {
        productField = productFields[0];
    } else {
        // 如果没找到，使用第一个非数值字段
        productField = fields.find(field => 
            typeof data[0][field] === 'string' && 
            !field.includes('象限') &&
            !field.includes('区间')
        );
    }
    
    console.log('🎯 使用产品字段:', productField);
    
    if (!productField) {
        console.error('❌ 无法找到产品字段');
        return;
    }
    
    // 获取表格元素
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');
    
    if (!tableHeader || !tableBody) {
        console.error('❌ 找不到表格元素');
        return;
    }
    
    // 定义列配置
    const columnConfig = [
        { key: productField, label: '产品名称', type: 'text', width: '200px' },
        { key: '象限名称', label: '象限分类', type: 'badge', width: '120px' },
        { key: '销量(吨)', label: '销量(吨)', type: 'number', width: '100px' },
        { key: '总金额(万元)', label: '总金额(万元)', type: 'number', width: '120px' },
        { key: '总毛利(万元)', label: '总毛利(万元)', type: 'profit', width: '120px' },
        { key: '吨毛利', label: '吨毛利(元)', type: 'profit', width: '120px' }
    ];
    
    // 过滤存在的列
    const availableColumns = columnConfig.filter(col => 
        data[0].hasOwnProperty(col.key)
    );
    
    console.log('📋 可用列:', availableColumns.map(c => c.label));
    
    // 生成表头
    let headerHtml = '<tr>';
    availableColumns.forEach(col => {
        headerHtml += `
            <th style="min-width: ${col.width}; text-align: ${col.type === 'text' ? 'left' : 'right'};">
                ${col.label}
            </th>
        `;
    });
    headerHtml += '</tr>';
    tableHeader.innerHTML = headerHtml;
    
    // 生成表格数据
    let bodyHtml = '';
    data.slice(0, 50).forEach((row, index) => {
        bodyHtml += '<tr>';
        availableColumns.forEach(col => {
            const value = row[col.key];
            let displayValue = value;
            let cellStyle = '';
            let cellClass = '';
            
            // 根据类型格式化值
            switch (col.type) {
                case 'number':
                    if (typeof value === 'number') {
                        displayValue = value.toFixed(2);
                        cellStyle = 'text-align: right;';
                    }
                    break;
                    
                case 'profit':
                    if (typeof value === 'number') {
                        displayValue = Math.round(value);
                        cellStyle = 'text-align: right;';
                        cellClass = value >= 0 ? 'profit-positive' : 'profit-negative';
                    }
                    break;
                    
                case 'badge':
                    if (value) {
                        const badgeClass = getBadgeClass(value);
                        displayValue = `<span class="quadrant-badge ${badgeClass}">${value}</span>`;
                        cellStyle = 'text-align: center;';
                    }
                    break;
                    
                default:
                    cellStyle = 'text-align: left;';
            }
            
            bodyHtml += `<td class="${cellClass}" style="${cellStyle}">${displayValue || ''}</td>`;
        });
        bodyHtml += '</tr>';
    });
    
    tableBody.innerHTML = bodyHtml;
    
    console.log('✅ 表格修复完成！显示了', Math.min(data.length, 50), '行数据');
}

// 3. 获取象限标签样式
function getBadgeClass(quadrantName) {
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

// 4. 修复列设置功能
function fixColumnSettings() {
    console.log('🔧 修复列设置功能...');
    
    const columnBtn = document.getElementById('columnSettingsBtn');
    const columnMenu = document.getElementById('columnSettingsMenu');
    
    if (!columnBtn || !columnMenu) {
        console.warn('⚠️ 列设置元素不存在');
        return;
    }
    
    // 简单的切换功能
    columnBtn.onclick = function(e) {
        e.stopPropagation();
        const isVisible = columnMenu.style.display === 'block';
        columnMenu.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            // 生成列选项
            const columnList = columnMenu.querySelector('.column-list');
            if (columnList) {
                columnList.innerHTML = `
                    <div class="column-group">
                        <h4 class="group-title">基础信息</h4>
                        <label class="column-option basic-column">
                            <input type="checkbox" checked disabled>
                            <span class="column-label">产品名称</span>
                            <small class="column-note">必显</small>
                        </label>
                        <label class="column-option basic-column">
                            <input type="checkbox" checked disabled>
                            <span class="column-label">象限分类</span>
                            <small class="column-note">必显</small>
                        </label>
                    </div>
                    <div class="column-group">
                        <h4 class="group-title">数值指标</h4>
                        <label class="column-option">
                            <input type="checkbox" checked>
                            <span class="column-label">销量(吨)</span>
                        </label>
                        <label class="column-option">
                            <input type="checkbox" checked>
                            <span class="column-label">总金额(万元)</span>
                        </label>
                        <label class="column-option">
                            <input type="checkbox" checked>
                            <span class="column-label">总毛利(万元)</span>
                        </label>
                        <label class="column-option">
                            <input type="checkbox" checked>
                            <span class="column-label">吨毛利(元)</span>
                        </label>
                    </div>
                `;
            }
        }
    };
    
    // 点击其他地方关闭
    document.onclick = function(e) {
        if (!columnMenu.contains(e.target) && !columnBtn.contains(e.target)) {
            columnMenu.style.display = 'none';
        }
    };
    
    console.log('✅ 列设置功能修复完成');
}

// 5. 执行修复
console.log('🚀 开始执行修复...');

try {
    fixTableDisplay();
    fixColumnSettings();
    console.log('🎉 修复完成！表格应该正常显示了');
    console.log('💡 如果还有问题，请刷新页面后重新运行此脚本');
} catch (error) {
    console.error('❌ 修复过程中出现错误:', error);
    console.log('🔄 请尝试刷新页面后重新分析数据');
}

// 6. 提供手动重新修复的函数
window.manualFix = function() {
    console.log('🔄 手动重新修复...');
    fixTableDisplay();
    fixColumnSettings();
};

console.log('📝 如需重新修复，请运行: manualFix()');