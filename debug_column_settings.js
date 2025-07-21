// 调试列设置功能的脚本
// 在浏览器控制台中执行此代码来诊断问题

console.log('=== 开始调试列设置功能 ===');

// 1. 检查关键DOM元素是否存在
const elements = {
    columnSettingsBtn: document.getElementById('columnSettingsBtn'),
    columnSettingsDropdown: document.getElementById('columnSettingsDropdown'),
    applyColumnSettings: document.getElementById('applyColumnSettings'),
    cancelColumnSettings: document.getElementById('cancelColumnSettings'),
    selectAllColumns: document.getElementById('selectAllColumns'),
    resetDefaultColumns: document.getElementById('resetDefaultColumns'),
    columnSettingsContent: document.getElementById('columnSettingsContent')
};

console.log('DOM元素检查:');
Object.entries(elements).forEach(([name, element]) => {
    console.log(`- ${name}: ${element ? '✓ 存在' : '✗ 不存在'}`);
});

// 2. 检查事件监听器是否绑定
console.log('\n事件监听器检查:');
if (elements.columnSettingsBtn) {
    // 获取元素上的事件监听器（这在某些浏览器中可能不可用）
    const events = getEventListeners ? getEventListeners(elements.columnSettingsBtn) : null;
    if (events) {
        console.log('columnSettingsBtn 事件监听器:', events);
    } else {
        console.log('无法获取事件监听器信息（浏览器不支持）');
    }
}

// 3. 检查全局函数是否定义
const functions = [
    'initializeColumnSettings',
    'showColumnSettings',
    'hideColumnSettings',
    'generateColumnSettingsContent',
    'selectAllColumns',
    'resetDefaultColumns',
    'applyColumnSettings',
    'getAllAvailableFieldConfig',
    'getTableFieldConfig'
];

console.log('\n函数定义检查:');
functions.forEach(funcName => {
    const isDefined = typeof window[funcName] === 'function';
    console.log(`- ${funcName}: ${isDefined ? '✓ 已定义' : '✗ 未定义'}`);
});

// 4. 检查全局变量
console.log('\n全局变量检查:');
console.log('- analysisResult:', window.analysisResult ? '✓ 有数据' : '✗ 无数据');
console.log('- currentAnalysisType:', window.currentAnalysisType || '未设置');
console.log('- userColumnSettings:', window.userColumnSettings || '未设置');

// 5. 尝试手动触发显示列设置
console.log('\n尝试手动触发显示列设置...');
try {
    if (typeof showColumnSettings === 'function') {
        showColumnSettings();
        console.log('✓ showColumnSettings 执行成功');
    } else {
        console.log('✗ showColumnSettings 函数未定义');
    }
} catch (error) {
    console.error('✗ 执行 showColumnSettings 时出错:', error);
}

// 6. 检查按钮点击事件
console.log('\n尝试模拟按钮点击...');
if (elements.columnSettingsBtn) {
    try {
        elements.columnSettingsBtn.click();
        console.log('✓ 按钮点击成功');
        
        // 检查下拉菜单是否显示
        setTimeout(() => {
            const dropdown = document.getElementById('columnSettingsDropdown');
            if (dropdown && dropdown.style.display !== 'none') {
                console.log('✓ 下拉菜单已显示');
            } else {
                console.log('✗ 下拉菜单未显示');
            }
        }, 100);
    } catch (error) {
        console.error('✗ 按钮点击出错:', error);
    }
}

console.log('\n=== 调试完成 ===');
console.log('如果看到错误信息，请复制并分享以便进一步诊断');
