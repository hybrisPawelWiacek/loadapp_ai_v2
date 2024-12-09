import os
import importlib
import pytest
from pathlib import Path

# Root directory of the project
PROJECT_ROOT = Path(__file__).parent.parent

def test_required_directories_exist():
    """Test that all required directories are present"""
    required_dirs = [
        'frontend',
        'backend',
        'backend/domain/entities',
        'backend/domain/services',
        'backend/infrastructure',
        'tests'
    ]
    
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_required_files_exist():
    """Test that all required configuration files are present"""
    required_files = [
        'requirements.txt',
        'backend/config.py',
        '.env.example'
    ]
    
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        assert full_path.exists(), f"File {file_path} does not exist"
        assert full_path.is_file(), f"{file_path} is not a file"

def test_required_dependencies():
    """Test that all required packages can be imported"""
    required_packages = [
        'flask',
        'flask_restful',
        'flask_cors',
        'streamlit',
        'structlog',
        'pytest',
        'sqlalchemy',
        'openai',
        'pydantic'
    ]
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError as e:
            pytest.fail(f"Required package '{package}' could not be imported: {str(e)}")

def test_config_environment_variables():
    """Test that config.py can load required environment variables"""
    from backend.config import Config
    
    # Test essential configurations
    assert hasattr(Config, 'FLASK_ENV'), "FLASK_ENV not defined in Config"
    assert hasattr(Config, 'DATABASE_URL'), "DATABASE_URL not defined in Config"
    assert hasattr(Config, 'API_PREFIX'), "API_PREFIX not defined in Config"
    assert hasattr(Config, 'FRONTEND_URL'), "FRONTEND_URL not defined in Config"
