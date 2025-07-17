# Project Structure

## Root Directory Layout
```
├── app.py                 # Main Flask application entry point
├── analyzer.py            # Core data analysis module (DataAnalyzer class)
├── exporter.py           # Excel report generation module
├── utils.py              # Utility functions and helpers
├── start.py              # Alternative startup script
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── CHANGELOG.md          # Version history
└── find_port.py          # Port detection utility
```

## Application Directories
```
├── templates/            # Jinja2 HTML templates
│   └── index.html       # Main application UI
├── static/              # Static web assets
│   ├── css/
│   │   └── style.css    # Main stylesheet
│   ├── js/
│   │   └── app.js       # Frontend JavaScript logic
│   ├── images/          # Image assets (empty)
│   └── favicon.ico      # Site favicon
├── uploads/             # User uploaded Excel files (auto-created)
└── exports/             # Generated analysis reports (auto-created)
```

## Data Directories
```
├── 实际上传excel/        # Sample Excel files for testing
│   ├── 出口部单品利润明细汇总1-5月.xlsx
│   ├── 定制类-客户+产品.xlsx
│   ├── 流通-按客户+单品.xlsx
│   └── 电商-按客户+单品.xlsx
```

## Documentation Files
- Chinese documentation files for features and fixes
- Markdown files describing system capabilities and modifications

## Code Organization

### Core Modules
- **app.py**: Flask routes, request handling, session management
- **analyzer.py**: DataAnalyzer class with analysis logic
- **exporter.py**: ReportExporter class for Excel generation
- **utils.py**: Helper functions for field detection, data processing

### Key Classes
- **DataAnalyzer**: Main analysis engine
  - Field detection and mapping
  - Data aggregation and processing
  - Quadrant analysis calculations
  - Pareto analysis and additional analytics

### File Naming Conventions
- Python files: snake_case
- HTML templates: lowercase
- CSS/JS files: lowercase
- Upload files: timestamp_originalname format
- Export files: 分析报告_timestamp.xlsx format

### Directory Management
- Upload and export directories are auto-created
- Temporary files stored with UUID-based session IDs
- File cleanup handled manually (no automatic cleanup)