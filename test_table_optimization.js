// 测试明细数据表格优化功能
console.log('=== 测试明细数据表格优化功能 ===');

// 测试函数
function testTableOptimization() {
    console.log('开始测试表格优化功能...');
    
    // 1. 测试getGroupFieldName函数
    console.log('\n1. 测试getGroupFieldName函数');
    if (typeof getGroupFieldName === 'function') {
        const groupFieldName = getGroupFieldName();
        console.log('✓ getGroupFieldName函数存在');
        console.log('  返回值:', groupFieldName);
    } else {
        console.error('✗ getGroupFieldName函数不存在');
    }
    
    // 2. 测试getAllAvailableFieldConfig函数
    console.log('\n2. 测试getAllAvailableFieldConfig函数');
    if (typeof getAllAvailableFieldConfig === 'function') {
        try {
            const allFields = getAllAvailableFieldConfig();
            console.log('✓ getAllAvailableFieldConfig函数存在');
            console.log('  可用字段数量:', allFields.length);
            console.log('  字段类别:', [...new Set(allFields.map(f => f.category))]);
        } catch (error) {
            console.error('✗ getAllAvailableFieldConfig函数执行出错:', error);
        }
    } else {
        console.error('✗ getAllAvailableFieldConfig函数不存在');
    }
    
    // 3. 测试列设置UI元素
    console.log('\n3. 测试列设置UI元素');
    const columnSettingsBtn = document.getElementById('columnSettingsBtn');
    const columnSettingsMenu = document.getElementById('columnSettingsMenu');
    
    if (columnSettingsBtn) {
        console.log('✓ 列设置按钮存在');
    } else {
        console.error('✗ 列设置按钮不存在');
    }
    
    if (columnSettingsMenu) {
        console.log('✓ 列设置菜单存在');
    } else {
        console.error('✗ 列设置菜单不存在');
    }
    
    // 4. 测试initializeColumnSettings函数
    console.log('\n4. 测试initializeColumnSettings函数');
    if (typeof initializeColumnSettings === 'function') {
        console.log('✓ initializeColumnSettings函数存在');
        try {
            initializeColumnSettings();
            console.log('✓ initializeColumnSettings函数执行成功');
        } catch (error) {
            console.error('✗ initializeColumnSettings函数执行出错:', error);
        }
    } else {
        console.error('✗ initializeColumnSettings函数不存在');
    }
    
    // 5. 测试toggleRowDetails函数
    console.log('\n5. 测试toggleRowDetails函数');
    if (typeof toggleRowDetails === 'function') {
        console.log('✓ toggleRowDetails函数存在');
    } else {
        console.error('✗ toggleRowDetails函数不存在');
    }
    
    // 6. 测试generateRowDetails函数
    console.log('\n6. 测试generateRowDetails函数');
    if (typeof generateRowDetails === 'function') {
        console.log('✓ generateRowDetails函数存在');
    } else {
        console.error('✗ generateRowDetails函数不存在');
    }
    
    // 7. 检查CSS样式
    console.log('\n7. 检查CSS样式');
    const testElements = [
        '.table-header',
        '.column-settings-btn',
        '.column-settings-menu',
        '.data-bar-container',
        '.expand-btn',
        '.row-details'
    ];
    
    testElements.forEach(selector => {
        const element = document.querySelector(selector);
        if (element || document.styleSheets.length > 0) {
            console.log(`✓ 样式 ${selector} 可能存在`);
        } else {
            console.log(`? 样式 ${selector} 状态未知`);
        }
    });
    
    // 8. 测试数据结构
    console.log('\n8. 测试数据结构');
    if (typeof analysisResult !== 'undefined' && analysisResult) {
        console.log('✓ analysisResult存在');
        if (analysisResult.aggregated_data) {
            console.log('✓ aggregated_data存在，行数:', analysisResult.aggregated_data.length);
            if (analysisResult.aggregated_data.length > 0) {
                console.log('  示例数据字段:', Object.keys(analysisResult.aggregated_data[0]));
            }
        } else {
            console.log('? aggregated_data不存在');
        }
        
        if (analysisResult.field_detection) {
            console.log('✓ field_detection存在');
            console.log('  检测到的字段:', analysisResult.field_detection.detected_fields);
        } else {
            console.log('? field_detection不存在');
        }
    } else {
        console.log('? analysisResult不存在或为空');
    }
    
    // 9. 测试当前分析类型
    console.log('\n9. 测试当前分析类型');
    if (typeof currentAnalysisType !== 'undefined') {
        console.log('✓ currentAnalysisType存在:', currentAnalysisType);
    } else {
        console.log('? currentAnalysisType不存在');
    }
    
    console.log('\n=== 测试完成 ===');
}

// 手动测试列设置功能
function testColumnSettings() {
    console.log('\n=== 手动测试列设置功能 ===');
    
    const columnSettingsBtn = document.getElementById('columnSettingsBtn');
    if (columnSettingsBtn) {
        console.log('点击列设置按钮...');
        columnSettingsBtn.click();
        
        setTimeout(() => {
            const menu = document.getElementById('columnSettingsMenu');
            if (menu && menu.style.display === 'block') {
                console.log('✓ 列设置菜单成功显示');
                
                // 检查菜单内容
                const checkboxes = menu.querySelectorAll('input[type="checkbox"]');
                console.log('✓ 找到复选框数量:', checkboxes.length);
                
                const categories = menu.querySelectorAll('.column-category');
                console.log('✓ 找到类别数量:', categories.length);
                
                // 关闭菜单
                columnSettingsBtn.click();
            } else {
                console.error('✗ 列设置菜单未显示');
            }
        }, 100);
    } else {
        console.error('✗ 列设置按钮不存在');
    }
}

// 手动测试行详情功能
function testRowDetails() {
    console.log('\n=== 手动测试行详情功能 ===');
    
    const expandBtns = document.querySelectorAll('.expand-btn');
    if (expandBtns.length > 0) {
        console.log('✓ 找到展开按钮数量:', expandBtns.length);
        
        // 测试第一个展开按钮
        const firstBtn = expandBtns[0];
        console.log('点击第一个展开按钮...');
        firstBtn.click();
        
        setTimeout(() => {
            const detailsRows = document.querySelectorAll('.row-details[style*="table-row"]');
            if (detailsRows.length > 0) {
                console.log('✓ 行详情成功显示');
                
                // 检查详情内容
                const detailsContent = detailsRows[0].querySelector('.row-details-content');
                if (detailsContent) {
                    console.log('✓ 详情内容存在');
                    const detailItems = detailsContent.querySelectorAll('.detail-item');
                    console.log('✓ 详情项目数量:', detailItems.length);
                }
                
                // 关闭详情
                firstBtn.click();
            } else {
                console.error('✗ 行详情未显示');
            }
        }, 100);
    } else {
        console.error('✗ 未找到展开按钮');
    }
}

// 执行测试
testTableOptimization();

// 提供手动测试函数
window.testColumnSettings = testColumnSettings;
window.testRowDetails = testRowDetails;
window.testTableOptimization = testTableOptimization;

console.log('\n可用的手动测试函数:');
console.log('- testColumnSettings() - 测试列设置功能');
console.log('- testRowDetails() - 测试行详情功能');
console.log('- testTableOptimization() - 重新运行完整测试');
