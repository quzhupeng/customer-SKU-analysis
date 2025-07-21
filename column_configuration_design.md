# Enhanced Column Configuration Interface Design

## Overview
This document outlines the design for an enhanced column configuration feature that allows users to dynamically select and map Excel columns to analysis fields before and during analysis.

## Key Features

### 1. Pre-Analysis Column Mapping
- **Column Discovery**: Display all available columns from uploaded Excel file
- **Field Mapping Interface**: Allow users to map Excel columns to required analysis fields
- **Validation**: Real-time validation of required vs optional fields
- **Preview**: Show sample data for each column to help users make informed decisions

### 2. Dynamic Field Mapping
- **Drag & Drop**: Intuitive drag-and-drop interface for mapping columns to fields
- **Smart Suggestions**: AI-powered suggestions based on column names and content
- **Manual Override**: Allow users to override automatic field detection
- **Multiple Mapping**: Support mapping multiple columns to the same field type (with priority)

### 3. Flexible Validation System
- **Required Fields**: Clear indication of which fields are required for each analysis type
- **Optional Fields**: Show optional fields that enhance analysis but aren't required
- **Conditional Requirements**: Different field requirements based on analysis type
- **Graceful Degradation**: Allow analysis to proceed with missing optional fields

## User Interface Components

### 1. Column Configuration Modal
```
┌─────────────────────────────────────────────────────────────┐
│ Column Configuration                                    [×] │
├─────────────────────────────────────────────────────────────┤
│ Available Columns          │  Field Mapping               │
│ ┌─────────────────────────┐ │ ┌─────────────────────────┐   │
│ │ □ 客户名称              │ │ │ 🔴 Customer (Required)  │   │
│ │ □ 产品名称              │ │ │ [客户名称] [×]          │   │
│ │ □ 销售数量              │ │ │                         │   │
│ │ □ 销售金额              │ │ │ 🔴 Product (Required)   │   │
│ │ □ 毛利                  │ │ │ [产品名称] [×]          │   │
│ │ □ 地区                  │ │ │                         │   │
│ │ □ 成本                  │ │ │ 🔴 Quantity (Required)  │   │
│ │ □ 单价                  │ │ │ [销售数量] [×]          │   │
│ │ ...                     │ │ │                         │   │
│ └─────────────────────────┘ │ │ 🟡 Amount (Optional)    │   │
│                             │ │ [销售金额] [×]          │   │
│ Column Preview:             │ │                         │   │
│ ┌─────────────────────────┐ │ │ 🟡 Profit (Optional)    │   │
│ │ 客户名称: 春雪食品      │ │ │ [毛利] [×]              │   │
│ │          华润万家      │ │ │                         │   │
│ │          沃尔玛        │ │ │ 🟢 Region (Optional)    │   │
│ └─────────────────────────┘ │ │ [地区] [×]              │   │
│                             │ └─────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ Analysis Type: [Customer Analysis ▼]                       │
│ ✓ All required fields mapped  ⚠ 2 optional fields unmapped │
├─────────────────────────────────────────────────────────────┤
│                    [Cancel] [Save Configuration] [Analyze] │
└─────────────────────────────────────────────────────────────┘
```

### 2. Field Mapping Cards
Each field will have a dedicated card showing:
- **Field Type**: Customer, Product, Quantity, etc.
- **Requirement Level**: Required (🔴), Recommended (🟡), Optional (🟢)
- **Current Mapping**: Which Excel column is mapped
- **Sample Data**: Preview of data from mapped column
- **Validation Status**: Whether mapping is valid

### 3. Column Selection Panel
- **Checkbox List**: All available Excel columns with checkboxes
- **Search/Filter**: Search columns by name or content
- **Data Type Detection**: Show detected data types (text, number, date)
- **Sample Preview**: Show sample values for selected column
- **Usage Indicator**: Show which fields the column is mapped to

## Technical Implementation

### 1. New API Endpoints

#### `/api/column_configuration`
- **GET**: Retrieve current column configuration for a file
- **POST**: Save column configuration preferences
- **PUT**: Update existing column configuration

#### `/api/field_mapping`
- **POST**: Validate field mapping configuration
- **GET**: Get suggested field mappings for columns

#### `/api/column_preview`
- **POST**: Get preview data for specific columns

### 2. Data Structures

#### Column Configuration Object
```javascript
{
  fileId: "uuid",
  sheetName: "分客户",
  selectedColumns: ["客户名称", "产品名称", "销售数量", "销售金额"],
  fieldMappings: {
    customer: "客户名称",
    product: "产品名称", 
    quantity: "销售数量",
    amount: "销售金额",
    profit: null,
    region: null
  },
  analysisType: "customer",
  validationStatus: {
    isValid: true,
    requiredFieldsMapped: true,
    missingRequired: [],
    missingOptional: ["profit", "region"]
  },
  sessionId: "session_uuid",
  timestamp: "2025-07-18T10:30:00Z"
}
```

#### Field Definition Object
```javascript
{
  fieldType: "customer",
  label: "客户字段",
  description: "用于标识不同客户的字段",
  requirement: "required", // required, recommended, optional
  analysisTypes: ["customer", "region"],
  dataTypes: ["string"],
  aliases: ["客户名称", "客户", "客户全称"],
  validation: {
    allowEmpty: false,
    minUniqueValues: 2,
    maxLength: 100
  }
}
```

### 3. Session Management
- Store column configurations in session storage
- Persist preferences during current session
- Clear configurations on new file upload
- Support multiple file configurations simultaneously

## User Experience Flow

### 1. Initial Setup Flow
1. User uploads Excel file
2. System displays sheet selection
3. User selects sheet and clicks "Configure Columns"
4. Column configuration modal opens
5. System shows auto-detected field mappings
6. User reviews and adjusts mappings
7. User saves configuration and proceeds to analysis

### 2. Mid-Analysis Reconfiguration
1. User clicks "Column Settings" in analysis view
2. Configuration modal opens with current settings
3. User modifies column selections or field mappings
4. System validates changes
5. User applies changes
6. Analysis views refresh with new configuration

### 3. Error Handling
- **Missing Required Fields**: Clear error messages with suggestions
- **Invalid Data Types**: Warnings about potential data type mismatches
- **Empty Columns**: Alerts about columns with no data
- **Duplicate Mappings**: Handle multiple columns mapped to same field

## Validation Rules

### 1. Required Field Validation
- **Product Analysis**: Requires product field + at least one numeric field
- **Customer Analysis**: Requires customer field + at least one numeric field  
- **Region Analysis**: Requires region field + at least one numeric field

### 2. Data Quality Validation
- **Non-empty Columns**: Warn if selected columns are mostly empty
- **Data Type Consistency**: Check if column data matches expected field type
- **Unique Values**: Ensure categorical fields have reasonable number of unique values

### 3. Analysis Type Compatibility
- **Field Availability**: Show only relevant fields for selected analysis type
- **Conditional Requirements**: Adjust required fields based on analysis type
- **Cross-validation**: Ensure field combinations make sense for analysis

## Benefits

### 1. User Control
- Full control over which columns to include in analysis
- Ability to override automatic field detection
- Flexible mapping of columns to analysis fields

### 2. Data Quality
- Preview data before analysis to catch issues early
- Validate field mappings before processing
- Handle missing or incomplete data gracefully

### 3. Flexibility
- Support various Excel file structures
- Adapt to different naming conventions
- Work with partial data sets

### 4. User Experience
- Intuitive drag-and-drop interface
- Clear visual feedback on validation status
- Contextual help and suggestions
