# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Install dependencies**: `pip install -r requirements.txt`
- **Run the application**: `python app.py`
- **Access the app**: `http://localhost:5000`

## Architecture Overview

- **Backend**: Flask-based server with Pandas for data analysis and OpenPyXL for Excel handling.
- **Frontend**: Static HTML/CSS/JavaScript with ECharts for visualization.
- **Data Flow**: Excel files are processed by the backend, analyzed, and results are visualized in the frontend.