"""
Test cases for the new debugging functionality in obsidian-spec-mcp.
"""

import pytest
from obsidian_spec_mcp.server import detect_error_pattern, debug_mermaid, validate_obsidian_markdown, ERROR_PATTERNS


class TestErrorPatternDetection:
    """Test error pattern detection functionality."""
    
    def test_mermaid_lexical_error_pattern(self):
        """Test detection of Mermaid lexical errors."""
        error_msg = "Lexical error on line 3. Unrecognized text."
        result = detect_error_pattern(error_msg)
        
        assert result["pattern_found"] is True
        assert result["tool"] == "validate_obsidian_markdown"
        assert "mermaid" in result["packs"]
        assert "Lexical error on line" in result["matched_pattern"]
    
    def test_mermaid_parsing_error_pattern(self):
        """Test detection of Mermaid parsing errors."""
        error_msg = "Error parsing Mermaid diagram! Lexical error on line 3."
        result = detect_error_pattern(error_msg)
        
        assert result["pattern_found"] is True
        assert result["tool"] == "debug_mermaid"
        assert "mermaid" in result["packs"]
    
    def test_templater_error_pattern(self):
        """Test detection of Templater errors."""
        error_msg = "Unbalanced Templater tags in template"
        result = detect_error_pattern(error_msg)
        
        assert result["pattern_found"] is True
        assert result["tool"] == "validate_obsidian_markdown"
        assert "templater" in result["packs"]
    
    def test_tasks_error_pattern(self):
        """Test detection of Tasks errors."""
        error_msg = "Tasks metadata markers not found"
        result = detect_error_pattern(error_msg)
        
        assert result["pattern_found"] is True
        assert result["tool"] == "validate_obsidian_markdown"
        assert "tasks" in result["packs"]
    
    def test_unknown_error_pattern(self):
        """Test handling of unknown error patterns."""
        error_msg = "Some unknown error occurred"
        result = detect_error_pattern(error_msg)
        
        assert result["pattern_found"] is False
        assert result["tool"] == "validate_obsidian_markdown"
        assert "core" in result["packs"]
        assert "mermaid" in result["packs"]


class TestEnhancedValidation:
    """Test enhanced validation with auto-fix suggestions."""
    
    def test_mermaid_special_character_fix(self):
        """Test auto-fix for unquoted special characters in Mermaid."""
        markdown = """```mermaid
flowchart TD
    A[Start] --> B{/route}
    B --> C[End]
```"""
        
        result = validate_obsidian_markdown(markdown, packs=["mermaid"])
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert len(result["suggested_fixes"]) > 0
        
        # Check that the fix is suggested
        fix = result["suggested_fixes"][0]
        assert '"/route"' in fix["fixed"]
        assert "/route" in fix["original"]
        assert "special character" in fix["explanation"].lower()
    
    def test_no_fixes_for_valid_code(self):
        """Test that valid code returns no suggested fixes."""
        markdown = """```mermaid
flowchart TD
    A[Start] --> B["/route"]
    B --> C[End]
```"""
        
        result = validate_obsidian_markdown(markdown, packs=["mermaid"])
        
        assert result["valid"] is True
        assert len(result["suggested_fixes"]) == 0
    
    def test_multiple_special_characters(self):
        """Test fixing multiple special characters."""
        markdown = """```mermaid
flowchart TD
    A[Start] --> B{/route}
    B --> C[#tag]
    C --> D{:config}
```"""
        
        result = validate_obsidian_markdown(markdown, packs=["mermaid"])
        
        assert result["valid"] is False
        assert len(result["suggested_fixes"]) >= 2
        
        # Check that multiple fixes are suggested
        fixed_labels = [fix["fixed"] for fix in result["suggested_fixes"]]
        assert any('"/route"' in fix for fix in fixed_labels)
        assert any('"#tag"' in fix for fix in fixed_labels)
        assert any('":config"' in fix for fix in fixed_labels)


class TestDebugMermaid:
    """Test the debug_mermaid tool."""
    
    def test_simple_lexical_error(self):
        """Test debugging a simple lexical error."""
        markdown = """```mermaid
flowchart TD
    A[Start] --> B{/route}
```"""
        
        result = debug_mermaid(markdown)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert len(result["suggested_fixes"]) > 0
        assert len(result["debug_steps"]) > 0
        assert '"/route"' in result["corrected_code"]
    
    def test_complex_diagram_with_errors(self):
        """Test debugging a more complex diagram with multiple errors."""
        markdown = """```mermaid
flowchart TD
    A[Start] --> B{/route}
    B --> C[#tag]
    C --> D{:config}
    D --> E[End]
```"""
        
        result = debug_mermaid(markdown)
        
        assert result["valid"] is False
        assert len(result["suggested_fixes"]) >= 2
        assert '"/route"' in result["corrected_code"]
        assert '"#tag"' in result["corrected_code"]
        assert '":config"' in result["corrected_code"]
    
    def test_valid_diagram(self):
        """Test debugging a valid diagram."""
        markdown = """```mermaid
flowchart TD
    A[Start] --> B["/route"]
    B --> C[End]
```"""
        
        result = debug_mermaid(markdown)
        
        assert result["valid"] is True
        assert len(result["suggested_fixes"]) == 0
        assert result["corrected_code"] == markdown
    
    def test_debug_summary(self):
        """Test that debug summary is accurate."""
        markdown = """```mermaid
flowchart TD
    A[Start] --> B{/route}
```"""
        
        result = debug_mermaid(markdown)
        
        if result["suggested_fixes"]:
            assert "fixable issues" in result["summary"].lower()
            assert str(len(result["suggested_fixes"])) in result["summary"]
        else:
            assert "no syntax errors" in result["summary"].lower()


class TestErrorPatterns:
    """Test the error pattern library."""
    
    def test_error_patterns_structure(self):
        """Test that error patterns have the required structure."""
        for pattern, config in ERROR_PATTERNS.items():
            assert "tool" in config
            assert "packs" in config
            assert "message" in config
            assert "suggestion" in config
            assert isinstance(config["packs"], list)
    
    def test_mermaid_patterns(self):
        """Test Mermaid-specific error patterns."""
        assert "Lexical error on line" in ERROR_PATTERNS
        assert "Error parsing Mermaid diagram" in ERROR_PATTERNS
        
        lexical_config = ERROR_PATTERNS["Lexical error on line"]
        assert lexical_config["tool"] == "validate_obsidian_markdown"
        assert "mermaid" in lexical_config["packs"]
        
        parsing_config = ERROR_PATTERNS["Error parsing Mermaid diagram"]
        assert parsing_config["tool"] == "debug_mermaid"
        assert "mermaid" in parsing_config["packs"]


class TestIntegration:
    """Integration tests for the debugging workflow."""
    
    def test_full_debugging_workflow(self):
        """Test the complete debugging workflow from error to fix."""
        # Step 1: Detect error pattern
        error_msg = "Lexical error on line 3. Unrecognized text."
        pattern_result = detect_error_pattern(error_msg)
        
        assert pattern_result["pattern_found"] is True
        
        # Step 2: Debug the broken code
        broken_markdown = """```mermaid
flowchart TD
    A[Start] --> B{/route}
```"""
        
        debug_result = debug_mermaid(broken_markdown)
        assert debug_result["valid"] is False
        assert len(debug_result["suggested_fixes"]) > 0
        
        # Step 3: Validate the corrected code
        corrected_code = debug_result["corrected_code"]
        validation_result = validate_obsidian_markdown(corrected_code, packs=["mermaid"])
        
        assert validation_result["valid"] is True
    
    def test_error_pattern_to_tool_mapping(self):
        """Test that error patterns correctly map to appropriate tools."""
        test_cases = [
            ("Lexical error on line 3", "validate_obsidian_markdown"),
            ("Error parsing Mermaid diagram", "debug_mermaid"),
            ("Unbalanced Templater tags", "validate_obsidian_markdown"),
            ("Tasks metadata markers", "validate_obsidian_markdown"),
        ]
        
        for error_msg, expected_tool in test_cases:
            result = detect_error_pattern(error_msg)
            assert result["tool"] == expected_tool


if __name__ == "__main__":
    pytest.main([__file__])
