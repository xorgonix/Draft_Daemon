"""
Parser utilities for extracting structured content from LLM responses.
"""

import re


def extract_markdown_spec(text: str) -> str:
    """
    Extract markdown content from LLM response.
    
    Handles various backtick combinations:
    - ```markdown ... ```
    - ````markdown ... ````
    - ``` ... ```
    - Even nested or malformed backticks
    
    Args:
        text: The LLM response text
        
    Returns:
        str: The extracted markdown content (without the code block markers)
    """
    if not text:
        return ""
    
    # Pattern 1: Try ```markdown or ````markdown (with language specifier)
    # Matches 3 or more backticks, optional language, content, closing backticks
    pattern_with_lang = r"`{3,}(markdown)?\s*(.*?)\s*`{3,}"
    match = re.search(pattern_with_lang, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(2).strip()
    
    # Pattern 2: Try generic code blocks without language specifier
    pattern_generic = r"`{3,}\s*(.*?)\s*`{3,}"
    match = re.search(pattern_generic, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # Pattern 3: Look for content between any backtick sequences
    # This handles edge cases with varying backtick counts
    backtick_pattern = r"(`{3,})\s*(.*?)\s*\1"
    match = re.search(backtick_pattern, text, re.DOTALL)
    
    if match:
        return match.group(2).strip()
    
    # Fallback: If no code blocks found, return the entire text
    # This handles cases where LLM outputs raw markdown without wrapping
    return text.strip()


def extract_project_name(spec_content: str) -> str:
    """
    Extract project name from spec content.
    
    Looks for:
    1. First H1 header (# Project Name)
    2. First H2 header (## Project Name)
    3. Falls back to "Untitled_Project"
    
    Args:
        spec_content: The markdown spec content
        
    Returns:
        str: Sanitized project name suitable for filenames
    """
    if not spec_content:
        return "Untitled_Project"
    
    # Try H1 header first
    h1_pattern = r"^#\s+(.+?)\s*$"
    match = re.search(h1_pattern, spec_content, re.MULTILINE)
    
    if match:
        return _sanitize_filename(match.group(1))
    
    # Try H2 header
    h2_pattern = r"^##\s+(.+?)\s*$"
    match = re.search(h2_pattern, spec_content, re.MULTILINE)
    
    if match:
        return _sanitize_filename(match.group(1))
    
    return "Untitled_Project"


def _sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.
    
    - Replace spaces with underscores
    - Remove or replace invalid characters
    - Limit length
    
    Args:
        name: The original name
        
    Returns:
        str: Sanitized filename-safe string
    """
    # Replace spaces with underscores
    sanitized = name.replace(" ", "_")
    
    # Remove invalid filename characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", sanitized)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")
    
    # Limit length (Windows MAX_PATH is 260, but we want to be safe)
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    return sanitized or "Untitled_Project"


def is_spec_complete(text: str) -> bool:
    """
    Check if the LLM response indicates spec completion.
    
    Looks for:
    - Markdown code blocks (indicates final spec output)
    - Completion markers
    - Resolution keywords
    
    Args:
        text: The LLM response text
        
    Returns:
        bool: True if spec appears complete
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for markdown code blocks
    if "```markdown" in text_lower or "````markdown" in text_lower:
        return True
    
    # Check for explicit completion markers
    completion_markers = [
        "[spec_complete]",
        "spec is complete",
        "specification complete",
        "here is your spec",
        "here is the specification",
        "final specification",
    ]
    
    if any(marker in text_lower for marker in completion_markers):
        return True
    
    # Check for resolution commands
    resolution_keywords = [
        "resolve",
        "generate the spec",
        "generate spec",
        "output the spec",
    ]
    
    if any(keyword in text_lower for keyword in resolution_keywords):
        return True
    
    return False


# Test function
def _test_parser():
    """Test the parser with various inputs."""
    
    # Test 1: Standard markdown block
    test1 = """Here's your spec:

```markdown
# My Project
## Overview
This is a test project.
```

Hope this helps!"""
    
    result1 = extract_markdown_spec(test1)
    print(f"Test 1: {result1}")
    assert "# My Project" in result1
    
    # Test 2: Quadruple backticks
    test2 = """````markdown
# Another Project
Content here.
````"""
    
    result2 = extract_markdown_spec(test2)
    print(f"Test 2: {result2}")
    assert "# Another Project" in result2
    
    # Test 3: No code blocks (raw markdown)
    test3 = "# Raw Project\nThis is raw markdown."
    result3 = extract_markdown_spec(test3)
    print(f"Test 3: {result3}")
    assert "# Raw Project" in result3
    
    # Test 4: Spec completion detection
    assert is_spec_complete("```markdown\n# Spec\n```") == True
    assert is_spec_complete("The spec is complete.") == True
    assert is_spec_complete("Let me ask another question.") == False
    
    print("All tests passed!")


if __name__ == "__main__":
    _test_parser()
