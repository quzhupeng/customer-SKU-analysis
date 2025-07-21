// 诊断文件上传问题的脚本

console.log('=== 开始诊断文件上传问题 ===');

// 1. 检查DOM元素是否存在
console.log('检查DOM元素:');
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
console.log('- fileInput 存在:', !!fileInput);
console.log('- uploadArea 存在:', !!uploadArea);

if (fileInput) {
    console.log('- fileInput 类型:', fileInput.type);
    console.log('- fileInput accept:', fileInput.accept);
    console.log('- fileInput 事件监听器数量:', getEventListeners ? getEventListeners(fileInput) : '无法检查');
}

// 2. 检查函数是否存在
console.log('\n检查关键函数:');
console.log('- handleFileSelect 存在:', typeof handleFileSelect);
console.log('- uploadFile 存在:', typeof uploadFile);
console.log('- initializeEventListeners 存在:', typeof initializeEventListeners);

// 3. 检查是否有JavaScript错误
console.log('\n检查错误状态:');
window.addEventListener('error', function(e) {
    console.error('JavaScript错误:', e.error);
});

// 4. 手动测试文件选择
console.log('\n手动绑定文件选择事件:');
if (fileInput) {
    // 移除现有事件监听器（如果有的话）
    fileInput.removeEventListener('change', handleFileSelect);
    
    // 重新绑定
    fileInput.addEventListener('change', function(event) {
        console.log('文件选择事件触发!');
        const file = event.target.files[0];
        if (file) {
            console.log('选择的文件:', file.name, file.size, file.type);
            
            // 调用上传函数
            if (typeof uploadFile === 'function') {
                console.log('调用 uploadFile 函数...');
                uploadFile(file);
            } else {
                console.error('uploadFile 函数不存在!');
            }
        } else {
            console.log('没有选择文件');
        }
    });
    
    console.log('✓ 重新绑定文件选择事件完成');
}

// 5. 检查上传区域点击事件
if (uploadArea) {
    const button = uploadArea.querySelector('button');
    if (button) {
        console.log('- 上传按钮存在:', !!button);
        button.addEventListener('click', function() {
            console.log('上传按钮被点击');
            if (fileInput) {
                fileInput.click();
            }
        });
    }
}

// 6. 提供手动测试函数
window.testFileUpload = function() {
    console.log('手动测试文件上传...');
    if (fileInput) {
        fileInput.click();
    } else {
        console.error('文件输入元素不存在');
    }
};

console.log('\n=== 诊断完成 ===');
console.log('如果文件选择仍然没有反应，请:');
console.log('1. 检查浏览器控制台是否有错误信息');
console.log('2. 尝试运行: testFileUpload()');
console.log('3. 检查网络请求是否正常发送');