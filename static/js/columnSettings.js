// Enhanced Column Settings Module - Solution 1 Implementation
document.addEventListener('DOMContentLoaded', function() {
    const columnSettingsBtn = document.getElementById('columnSettingsBtn');
    const columnSettingsMenu = document.getElementById('columnSettingsMenu');
    const selectAllColumns = document.getElementById('selectAllColumns');
    const resetDefaultColumns = document.getElementById('resetDefaultColumns');
    const applyColumnSettings = document.getElementById('applyColumnSettings');
    const cancelColumnSettings = document.getElementById('cancelColumnSettings');
    
    // Enhanced toggle column settings menu with smooth animation
    columnSettingsBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        const isVisible = columnSettingsMenu.style.display === 'block';
        
        if (isVisible) {
            columnSettingsMenu.style.opacity = '0';
            columnSettingsMenu.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                columnSettingsMenu.style.display = 'none';
            }, 200);
        } else {
            columnSettingsMenu.style.display = 'block';
            setTimeout(() => {
                columnSettingsMenu.style.opacity = '1';
                columnSettingsMenu.style.transform = 'translateY(0)';
            }, 10);
            
            // Initialize column categories when opening
            initializeColumnCategories();
        }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!columnSettingsMenu.contains(e.target) && e.target !== columnSettingsBtn) {
            columnSettingsMenu.style.display = 'none';
        }
    });
    
    // Enhanced initialize column settings with categorization
    function initColumnSettings(columns) {
        // Store original column configuration
        window.originalColumns = columns;
        initializeColumnCategories();
    }
    
    // Initialize column categories based on field types
    function initializeColumnCategories() {
        const categoriesContainer = document.querySelector('.column-categories');
        if (!categoriesContainer) return;
        
        const columns = window.originalColumns || [];
        const categories = {
            '基础信息': [],
            '规模指标': [],
            '效率指标': [],
            '其他指标': []
        };
        
        // Categorize columns based on their type and purpose
        columns.forEach(column => {
            const columnId = column.id || column.key;
            const columnName = column.name || column.label;
            
            if (['item_name', 'customer_name', 'region_name', 'quadrant'].includes(columnId)) {
                categories['基础信息'].push({id: columnId, name: columnName});
            } else if (['quantity', 'amount', 'profit', 'total_cost'].includes(columnId)) {
                categories['规模指标'].push({id: columnId, name: columnName});
            } else if (['profit_per_unit', 'cost_rate', 'profit_margin'].includes(columnId)) {
                categories['效率指标'].push({id: columnId, name: columnName});
            } else {
                categories['其他指标'].push({id: columnId, name: columnName});
            }
        });
        
        // Get current visible columns
        const currentlyVisible = getCurrentVisibleColumns();
        
        // Render categories
        categoriesContainer.innerHTML = '';
        Object.keys(categories).forEach(categoryName => {
            if (categories[categoryName].length === 0) return;
            
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'column-category';
            
            const categoryHeader = document.createElement('div');
            categoryHeader.className = 'category-header';
            categoryHeader.innerHTML = `
                <span class="category-title">${categoryName}</span>
                <span class="category-count">(${categories[categoryName].length}项)</span>
            `;
            
            const columnList = document.createElement('div');
            columnList.className = 'category-columns';
            
            categories[categoryName].forEach(column => {
                const isVisible = currentlyVisible.includes(column.id);
                const columnItem = document.createElement('div');
                columnItem.className = 'column-item';
                columnItem.innerHTML = `
                    <label class="column-label">
                        <input type="checkbox" class="column-checkbox" 
                               data-column="${column.id}" 
                               ${isVisible ? 'checked' : ''}>
                        <span class="checkbox-custom"></span>
                        <span class="column-name">${column.name}</span>
                    </label>
                `;
                columnList.appendChild(columnItem);
            });
            
            categoryDiv.appendChild(categoryHeader);
            categoryDiv.appendChild(columnList);
            categoriesContainer.appendChild(categoryDiv);
        });
        
        // Add event listeners to all checkboxes
        setupColumnCheckboxes();
    }
    
    // Toggle column visibility
    function toggleColumnVisibility(columnId, isVisible) {
        const table = document.getElementById('dataTable');
        const headerCells = table.querySelectorAll('thead th');
        const bodyRows = table.querySelectorAll('tbody tr');
        
        headerCells.forEach((cell, index) => {
            if (cell.dataset.column === columnId) {
                cell.style.display = isVisible ? '' : 'none';
                
                // Update corresponding cells in each row
                bodyRows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells[index]) {
                        cells[index].style.display = isVisible ? '' : 'none';
                    }
                });
            }
        });
    }
    
    // Enhanced control button handlers
    selectAllColumns.addEventListener('click', function() {
        const checkboxes = document.querySelectorAll('.column-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        showMessage('已选择所有列', 'info');
    });
    
    resetDefaultColumns.addEventListener('click', function() {
        // Enhanced default visible columns including new optimization columns
        const defaultVisible = ['item_name', 'customer_name', '金额', '毛利', 'profit_per_unit'];
        const checkboxes = document.querySelectorAll('.column-checkbox');
        
        checkboxes.forEach(checkbox => {
            const columnId = checkbox.dataset.column;
            checkbox.checked = defaultVisible.includes(columnId);
        });
        showMessage('已重置为默认列配置', 'info');
    });
    
    applyColumnSettings.addEventListener('click', function() {
        applyColumnConfiguration();
        closeColumnSettings();
        showMessage('列配置已应用', 'success');
    });
    
    cancelColumnSettings.addEventListener('click', function() {
        closeColumnSettings();
    });
    
    // Get currently visible columns
    function getCurrentVisibleColumns() {
        const savedLayout = localStorage.getItem('columnLayout');
        if (savedLayout) {
            return JSON.parse(savedLayout);
        }
        // Enhanced default visible columns including new optimization columns
        return ['item_name', 'customer_name', '金额', '毛利', 'profit_per_unit'];
    }
    
    // Setup checkbox event listeners
    function setupColumnCheckboxes() {
        const checkboxes = document.querySelectorAll('.column-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // Visual feedback - don't apply immediately
                updateColumnPreview();
            });
        });
    }
    
    // Update column preview counter
    function updateColumnPreview() {
        const checkedBoxes = document.querySelectorAll('.column-checkbox:checked');
        const applyBtn = document.getElementById('applyColumnSettings');
        applyBtn.textContent = `应用 (${checkedBoxes.length}列)`;
    }
    
    // Apply column configuration
    function applyColumnConfiguration() {
        const visibleColumns = [];
        const checkboxes = document.querySelectorAll('.column-checkbox:checked');
        
        checkboxes.forEach(checkbox => {
            visibleColumns.push(checkbox.dataset.column);
        });
        
        // Save to localStorage
        localStorage.setItem('columnLayout', JSON.stringify(visibleColumns));
        
        // Apply to current table
        applyColumnVisibility(visibleColumns);
    }
    
    // Apply column visibility
    function applyColumnVisibility(visibleColumns) {
        const table = document.getElementById('dataTable');
        if (!table) return;
        
        const headerCells = table.querySelectorAll('thead th');
        const bodyRows = table.querySelectorAll('tbody tr');
        
        headerCells.forEach((cell, index) => {
            const columnId = cell.dataset.column;
            if (columnId) {
                const isVisible = visibleColumns.includes(columnId);
                cell.style.display = isVisible ? '' : 'none';
                
                // Update corresponding cells in each row
                bodyRows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells[index]) {
                        cells[index].style.display = isVisible ? '' : 'none';
                    }
                });
            }
        });
    }
    
    // Close column settings with animation
    function closeColumnSettings() {
        columnSettingsMenu.style.opacity = '0';
        columnSettingsMenu.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            columnSettingsMenu.style.display = 'none';
        }, 200);
    }
    
    // Apply saved layout
    function applySavedLayout() {
        const visibleColumns = getCurrentVisibleColumns();
        applyColumnVisibility(visibleColumns);
    }
    
    // Utility function for showing messages
    function showMessage(message, type = 'info') {
        // Use existing message system if available, otherwise create a simple alert
        if (window.showMessage && typeof window.showMessage === 'function') {
            window.showMessage(message, type);
        } else {
            // Fallback to console or alert
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    // Expose functions for external use
    window.columnSettings = {
        init: initColumnSettings,
        applySavedLayout: applySavedLayout,
        showMessage: showMessage
    };
});