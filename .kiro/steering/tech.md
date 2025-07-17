# Technology Stack

## Backend
- **Python 3.7+**: Core runtime
- **Flask 2.3.3**: Web framework for REST API and web server
- **Pandas 2.0.3**: Data processing and analysis
- **OpenPyXL 3.1.2**: Excel file reading/writing
- **NumPy 1.24.3**: Numerical computations
- **xlrd 2.0.1**: Legacy Excel file support

## Frontend
- **HTML5 + CSS3 + Vanilla JavaScript**: No frontend frameworks
- **ECharts**: Data visualization and charting library
- **Font Awesome 6.0.0**: Icons via CDN
- **Responsive Design**: Mobile-friendly UI

## Development Environment
- **File Structure**: Standard Flask application layout
- **Static Assets**: CSS, JS, images served from `/static`
- **Templates**: Jinja2 templating in `/templates`
- **File Uploads**: Handled via `/uploads` directory
- **Exports**: Generated reports saved to `/exports`

## Common Commands

### Setup & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Manual installation if needed
pip install Flask pandas openpyxl xlrd numpy
```

### Running the Application
```bash
# Standard startup
python app.py

# Alternative startup script
python start.py

# Development mode (debug enabled)
python app.py  # Debug is enabled by default in app.py
```

### Development Server
- **Default URL**: http://localhost:5000
- **Host**: 0.0.0.0 (accessible from network)
- **Port**: 8080 (configured in app.py)
- **Debug Mode**: Enabled by default

## Architecture Notes
- **Stateless Design**: Analysis results stored in memory with UUID-based session management
- **File Processing**: Synchronous Excel processing (no background tasks)
- **Error Handling**: Comprehensive try-catch blocks with user-friendly error messages
- **Logging**: Python logging module for debugging and monitoring