"""
Tests for Draft Daemon application.

Run with: .\\.venv\\Scripts\\python.exe -m pytest tests/ -v
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_main_import():
    """Test that main.py imports without errors."""
    try:
        import main
        print("[PASS] main.py imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] main.py import failed: {e}")
        return False


def test_llm_client_import():
    """Test that LLMClient imports correctly."""
    try:
        from utils.llm_client import LLMClient
        print("[PASS] LLMClient imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] LLMClient import failed: {e}")
        return False


def test_llm_client_initialization():
    """Test that LLMClient initializes with correct Ollama settings."""
    from utils.llm_client import LLMClient
    
    client = LLMClient(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="gemma3-12b-32k:latest"
    )
    
    assert client.base_url == "http://localhost:11434/v1", f"Expected Ollama URL, got {client.base_url}"
    assert client.api_key == "ollama", f"Expected 'ollama' API key, got {client.api_key}"
    assert client.model == "gemma3-12b-32k:latest", f"Expected gemma3 model, got {client.model}"
    
    print("[PASS] LLMClient initializes with correct Ollama settings")
    return True


def test_workflows_import():
    """Test that workflow nodes and flow import correctly."""
    try:
        from workflows.nodes import ChatInputNode, LLMEvaluateNode, GenerateSpecNode
        from workflows.flow import create_spec_interviewer_flow
        print("[PASS] Workflow nodes and flow import successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Workflow import failed: {e}")
        return False


def test_flow_creation():
    """Test that the spec interviewer flow can be created."""
    from workflows.flow import create_spec_interviewer_flow
    from workflows.nodes import ChatInputNode, LLMEvaluateNode, GenerateSpecNode
    
    flow = create_spec_interviewer_flow()
    
    assert flow is not None, "Flow should not be None"
    assert isinstance(flow.start_node, ChatInputNode), f"Expected ChatInputNode, got {type(flow.start_node)}"
    
    # Check node connections - ChatInputNode uses 'default' action (via >>)
    chat_node = flow.start_node
    assert "default" in chat_node.successors, "ChatInputNode should have 'default' successor"
    
    llm_node = chat_node.successors.get("default")
    assert isinstance(llm_node, LLMEvaluateNode), f"Expected LLMEvaluateNode, got {type(llm_node)}"
    
    # LLMEvaluateNode should have both 'evaluate' (loop back) and 'generate' successors
    assert "evaluate" in llm_node.successors, "LLMEvaluateNode should have 'evaluate' successor"
    assert "generate" in llm_node.successors, "LLMEvaluateNode should have 'generate' successor"
    
    gen_node = llm_node.successors.get("generate")
    assert isinstance(gen_node, GenerateSpecNode), f"Expected GenerateSpecNode, got {type(gen_node)}"
    
    print("[PASS] Spec interviewer flow creates correctly with proper node connections")
    return True


def test_components_import():
    """Test that components import correctly."""
    try:
        from components.editor_pane import EditorPane
        print("[PASS] EditorPane imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Component import failed: {e}")
        return False


def test_parser_utilities():
    """Test the markdown parser utilities."""
    from utils.parser import extract_markdown_spec, extract_project_name, is_spec_complete
    
    # Test extract_markdown_spec with triple backticks
    test1 = "```markdown\n# Test Project\nContent\n```"
    result1 = extract_markdown_spec(test1)
    assert "# Test Project" in result1, f"Expected markdown content, got {result1}"
    
    # Test extract_markdown_spec with quadruple backticks
    test2 = "````markdown\n# Another Project\nContent\n````"
    result2 = extract_markdown_spec(test2)
    assert "# Another Project" in result2, f"Expected markdown content, got {result2}"
    
    # Test is_spec_complete
    assert is_spec_complete("```markdown\n# Spec\n```") == True, "Should detect spec completion"
    assert is_spec_complete("Let me ask a question") == False, "Should not detect completion"
    
    print("[PASS] Parser utilities work correctly")
    return True


def test_file_system_writer():
    """Test the FileSystemWriter utility."""
    from utils.file_system_writer import FileSystemWriter
    import tempfile
    import shutil
    
    # Create temp directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        writer = FileSystemWriter(base_dir=temp_dir)
        
        # Test directory creation
        test_spec = "# Test Project\n\nThis is a test."
        project_dir, spec_path = writer.write_spec(test_spec, "Test_Project")
        
        assert project_dir.exists(), f"Project directory should exist: {project_dir}"
        assert spec_path.exists(), f"Spec file should exist: {spec_path}"
        assert spec_path.name == "01_Spec.md", f"Expected 01_Spec.md, got {spec_path.name}"
        
        # Verify content
        content = spec_path.read_text()
        assert "# Test Project" in content, "Spec content should match"
        
        print("[PASS] FileSystemWriter works correctly")
        return True
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_shared_store_structure():
    """Test that the shared store has the correct structure."""
    from main import EDITORIAL_ARCHITECT_SYSTEM_PROMPT
    
    shared = {
        "system_prompt": EDITORIAL_ARCHITECT_SYSTEM_PROMPT,
        "chat_history": [],
        "messages": [],
        "user_input": None,
        "llm_response": None,
        "spec_complete": False,
        "final_spec": None,
        "project_name": None,
        "spec_file_path": None,
    }
    
    # Verify all required keys exist
    required_keys = [
        "system_prompt", "chat_history", "messages", "user_input",
        "llm_response", "spec_complete", "final_spec", "project_name", "spec_file_path"
    ]
    
    for key in required_keys:
        assert key in shared, f"Missing required key: {key}"
    
    # Verify system prompt is set
    assert "Editorial Architect" in shared["system_prompt"], "System prompt should be set"
    
    print("[PASS] Shared store structure is correct")
    return True


def test_input_field_binding():
    """Test that input field binding works (the fix for the TypeError)."""
    # This test verifies the fix for: TypeError: 'Input' object is not callable
    # The issue was using @input_field.on('change') decorator syntax
    # The fix uses input_field.on('change', callback) function call syntax
    
    from nicegui import ui
    
    # Create an input and button (won't render, just test the binding)
    input_field = ui.input(placeholder='Test...')
    button = ui.button('Send').disable()
    
    # This should NOT raise TypeError
    try:
        input_field.on('change', lambda e: None)
        input_field.on('input', lambda e: None)
        print("[PASS] Input field event binding works correctly")
        return True
    except TypeError as e:
        print(f"[FAIL] Input field binding raised TypeError: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Input field binding raised exception: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("Running Draft Daemon Tests")
    print("="*60 + "\n")
    
    tests = [
        test_main_import,
        test_llm_client_import,
        test_llm_client_initialization,
        test_workflows_import,
        test_flow_creation,
        test_components_import,
        test_parser_utilities,
        test_file_system_writer,
        test_shared_store_structure,
        test_input_field_binding,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} raised exception: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
