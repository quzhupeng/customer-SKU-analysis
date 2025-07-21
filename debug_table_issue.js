// 调试表格显示问题的脚本

console.log('=== 开始调试表格显示问题 ===');

// 1. 检查全局变量
console.log('当前分析类型:', currentAnalysisType);
console.log('分析结果存在:', !!analysisResult);

if (analysisResult) {
    console.log('字段检测结果:', analysisResult.field_detection?.detected_fields);
    console.log('聚合数据数量:', analysisResult.aggregated_data?.length);
    
    if (analysisResult.aggregated_data && analysisResult.aggregated_data.length > 0) {
        const sample = analysisResult.aggregated_data[0];
        console.log('聚合数据示例字段:', Object.keys(sample));
        
        // 检查产品字段
        const groupFieldName = getGroupFieldName();
        console.log('获取到的分组字段名:', groupFieldName);
        
        if (groupFieldName && sample[groupFieldName]) {
            console.log('产品字段值示例:', sample[groupFieldName]);
        } else {
            console.error('产品字段不存在或为空');
        }
    }
}

// 2. 检查表格配置
console.log('\n=== 检查表格配置 ===');
try {
    const fieldConfig = getTableFieldConfig();
    console.log('表格字段配置:', fieldConfig.map(c => ({key: c.key, label: c.label})));
} catch (error) {
    console.error('获取表格配置失败:', error);
}

// 3. 检查列设置功能
console.log('\n=== 检查列设置功能 ===');
const columnSettingsBtn = document.getElementById('columnSettingsBtn');
const columnSettingsMenu = document.getElementById('columnSettingsMenu');

console.log('列设置按钮存在:', !!columnSettingsBtn);
console.log('列设置菜单存在:', !!columnSettingsMenu);

if (typeof initializeColumnSettings === 'function') {
    console.log('initializeColumnSettings 函数存在');
} else {
    console.error('initializeColumnSettings 函数不存在');
}

if (typeof getVisibleColumns === 'function') {
    console.log('getVisibleColumns 函数存在');
} else {
    console.error('getVisibleColumns 函数不存在');
}

// 4. 尝试手动修复表格显示
console.log('\n=== 尝试手动修复 ===');

function fixTableDisplay() {
    if (!analysisResult || !analysisResult.aggregated_data) {
        console.error('没有分析数据');
        return;
    }
    
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');
    
    if (!tableHeader || !tableBody) {
        console.error('表格元素不存在');
        return;
    }
    
    const data = analysisResult.aggregated_data;
    const sample = data[0];
    
    // 手动创建简单的表头
    const groupField = getGroupFieldName();
    const basicColumns = [
        {key: groupField, label: '产品名称'},
        {key: '象限名称', label: '象限分类'},
        {key: '销量(吨)', label: '销量(吨)'},
        {key: '总金额(万元)', label: '总金额(万元)'},
        {key: '总毛利(万元)', label: '总毛利(万元)'},
        {key: '吨毛利', label: '吨毛利(元)'}
    ];
    
    // 过滤存在的列
    const availableColumns = basicColumns.filter(col => sample.hasOwnProperty(col.key));
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
    data.slice(0, 10).forEach(row => { // 只显示前10行
        bodyHtml += '<tr>';
        availableColumns.forEach(col => {
            const value = row[col.key];
            let displayValue = value;
            
            // 格式化数值
            if (typeof value === 'number') {
                if (col.key.includes('吨毛利')) {
                    displayValue = Math.round(value);
                } else if (col.key.includes('万元') || col.key.includes('吨')) {
                    displayValue = value.toFixed(2);
                }
            }
            
            bodyHtml += `<td>${displayValue || ''}</td>`;
        });
        bodyHtml += '</tr>';
    });
    tableBody.innerHTML = bodyHtml;
    
    console.log('✓ 手动修复表格完成');
}

// 执行修复
fixTableDisplay();

console.log('=== 调试完成 ===');