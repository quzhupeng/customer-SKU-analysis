#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本
"""

import sys
import os

def test_imports():
    """测试导入"""
    try:
        print("测试导入...")
        from utils import safe_to_dict, validate_required_fields
        from analyzer import DataAnalyzer
        print("✓ 导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_field_validation():
    """测试字段验证"""
    try:
        print("测试字段验证...")
        from utils import validate_required_fields
        
        # 产品分析 - 应该通过
        product_fields = {'product': 'SKU', 'quantity': '数量', 'profit': '毛利'}
        missing = validate_required_fields(product_fields, 'product')
        assert len(missing) == 0, f"产品分析应该通过，但缺失: {missing}"
        
        # 客户分析 - 应该通过
        customer_fields = {'customer': '客户名称', 'amount': '金额', 'profit': '毛利'}
        missing = validate_required_fields(customer_fields, 'customer')
        assert len(missing) == 0, f"客户分析应该通过，但缺失: {missing}"
        
        # 不完整字段 - 应该失败
        incomplete_fields = {'product': 'SKU'}
        missing = validate_required_fields(incomplete_fields, 'product')
        assert len(missing) > 0, "不完整字段应该失败"
        
        print("✓ 字段验证测试通过")
        return True
    except Exception as e:
        print(f"✗ 字段验证测试失败: {e}")
        return False

def test_safe_conversion():
    """测试安全转换"""
    try:
        print("测试安全转换...")
        import pandas as pd
        import numpy as np
        from utils import safe_to_dict
        
        # 创建包含问题数据的DataFrame
        df = pd.DataFrame({
            'normal': [1, 2, 3],
            'nan_col': [1, np.nan, 3],
            'inf_col': [1, np.inf, -np.inf]
        })
        
        result = safe_to_dict(df)
        assert len(result) == 3, "应该有3条记录"
        assert result[1]['nan_col'] is None, "NaN应该转换为None"
        assert result[1]['inf_col'] is None, "inf应该转换为None"
        
        print("✓ 安全转换测试通过")
        return True
    except Exception as e:
        print(f"✗ 安全转换测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 快速测试 ===")
    
    tests = [
        test_imports,
        test_field_validation,
        test_safe_conversion
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("✓ 所有测试通过，可以启动应用")
        return True
    else:
        print("✗ 部分测试失败，请检查代码")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
