"""
FileSystemWriter utility for creating project directories and writing spec files.
"""

import os
import json
from datetime import datetime
from pathlib import Path

from utils.parser import extract_project_name


class FileSystemWriter:
    """
    Writes OpenSpec specifications to the file system.
    
    Creates directory structure:
    Writing_System_Dev/Projects/<project_name>/01_Spec.md
    
    If project_name is not provided or invalid, uses timestamp fallback.
    """
    
    def __init__(self, base_dir=None):
        """
        Initialize the FileSystemWriter.
        
        Args:
            base_dir: Base directory for projects (default: current dir/Writing_System_Dev/Projects)
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path.cwd() / "Writing_System_Dev" / "Projects"
    
    def ensure_base_directory(self) -> Path:
        """
        Ensure the base projects directory exists.
        
        Returns:
            Path: The base directory path
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        return self.base_dir
    
    def create_project_directory(self, project_name: str = None, spec_content: str = None) -> Path:
        """
        Create a project directory with timestamp fallback.
        
        Args:
            project_name: Optional project name (if None, extracts from spec_content or uses timestamp)
            spec_content: Optional spec content to extract project name from
            
        Returns:
            Path: The created project directory path
        """
        # Ensure base directory exists
        self.ensure_base_directory()
        
        # Determine project name
        if project_name:
            safe_name = self._sanitize_folder_name(project_name)
        elif spec_content:
            extracted_name = extract_project_name(spec_content)
            safe_name = self._sanitize_folder_name(extracted_name)
        else:
            # Timestamp fallback: YYYYMMDD_HHMMSS
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"Project_{timestamp}"
        
        # Handle duplicate directory names
        project_dir = self.base_dir / safe_name
        counter = 1
        while project_dir.exists():
            project_dir = self.base_dir / f"{safe_name}_v{counter}"
            counter += 1
        
        # Create the directory
        project_dir.mkdir(parents=True, exist_ok=True)
        
        return project_dir
    
    def write_spec(self, spec_content: str, project_name: str = None) -> tuple:
        """
        Write the specification to 01_Spec.md in a project directory.
        
        Args:
            spec_content: The markdown spec content to write
            project_name: Optional project name
            
        Returns:
            tuple: (project_directory_path, spec_file_path)
        """
        # Create project directory
        project_dir = self.create_project_directory(project_name, spec_content)
        
        # Write spec file
        spec_path = project_dir / "01_Spec.md"
        spec_path.write_text(spec_content, encoding="utf-8")
        
        return (project_dir, spec_path)
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize a string for use as a folder name.
        
        - Replace spaces with underscores
        - Remove invalid characters
        - Limit length
        
        Args:
            name: The original name
            
        Returns:
            str: Sanitized folder-safe string
        """
        # Replace spaces with underscores
        sanitized = name.replace(" ", "_")
        
        # Remove invalid folder name characters
        sanitized = ''.join(c for c in sanitized if c not in '<>:"/\\|?*')
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")
        
        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized or f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


# Test function
def _test_writer():
    """Test the FileSystemWriter."""
    writer = FileSystemWriter()
    
    test_spec = """# Test Project Specification

## Overview
This is a test specification.

## Requirements
- Requirement 1
- Requirement 2
"""
    
    project_dir, spec_path = writer.write_spec(test_spec, "Test_Project")
    
    print(f"Created directory: {project_dir}")
    print(f"Wrote spec: {spec_path}")
    print(f"Spec exists: {spec_path.exists()}")
    
    # Clean up test directory
    import shutil
    shutil.rmtree(project_dir)
    print("Test directory cleaned up.")


if __name__ == "__main__":
    _test_writer()
