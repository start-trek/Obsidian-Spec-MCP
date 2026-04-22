#!/usr/bin/env python3
"""
Test script to verify the new debugging tools work correctly with the original error case.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from obsidian_spec_mcp.server import detect_error_pattern, debug_mermaid, validate_obsidian_markdown

# Test case: The original error from the investigation
ORIGINAL_ERROR_MESSAGE = "Error parsing Mermaid diagram! Lexical error on line 3. Unrecognized text. ...xt, links, rationale]    C --> D{/route"

ORIGINAL_BROKEN_MARKDOWN = """```mermaid
flowchart TD
    A[context, text, links, rationale] --> C
    C --> D{/route}
```"""

def test_error_pattern_detection():
    """Test that error pattern detection correctly identifies Mermaid errors."""
    print("=== Testing Error Pattern Detection ===")
    
    result = detect_error_pattern(ORIGINAL_ERROR_MESSAGE)
    
    print(f"Pattern found: {result['pattern_found']}")
    print(f"Matched pattern: {result.get('matched_pattern', 'None')}")
    print(f"Tool: {result['tool']}")
    print(f"Packs: {result['packs']}")
    print(f"Message: {result['message']}")
    print(f"Suggestion: {result['suggestion']}")
    
    # Should detect "Lexical error on line" pattern
    assert result['pattern_found'] == True
    assert result['tool'] == 'validate_obsidian_markdown'
    assert 'mermaid' in result['packs']
    print("PASS: Error pattern detection working correctly\n")

def test_enhanced_validation():
    """Test that enhanced validation provides suggested fixes."""
    print("=== Testing Enhanced Validation ===")
    
    result = validate_obsidian_markdown(ORIGINAL_BROKEN_MARKDOWN, packs=['mermaid'])
    
    print(f"Valid: {result['valid']}")
    print(f"Issues found: {len(result['issues'])}")
    
    for issue in result['issues']:
        print(f"  - Line {issue['line']}: {issue['message']}")
    
    print(f"Suggested fixes: {len(result['suggested_fixes'])}")
    for fix in result['suggested_fixes']:
        print(f"  - Line {fix['line']}: {fix['original']} -> {fix['fixed']}")
        print(f"    Explanation: {fix['explanation']}")
    
    # Should detect the error and suggest a fix
    assert result['valid'] == False
    assert len(result['issues']) > 0
    assert len(result['suggested_fixes']) > 0
    assert '"/route"' in result['suggested_fixes'][0]['fixed']
    print("PASS: Enhanced validation working correctly\n")

def test_debug_mermaid():
    """Test the new debug_mermaid tool."""
    print("=== Testing debug_mermaid Tool ===")
    
    result = debug_mermaid(ORIGINAL_BROKEN_MARKDOWN)
    
    print(f"Valid: {result['valid']}")
    print(f"Issues: {len(result['issues'])}")
    print(f"Suggested fixes: {len(result['suggested_fixes'])}")
    print(f"Debug steps: {len(result['debug_steps'])}")
    print(f"Summary: {result['summary']}")
    
    print("\nCorrected code:")
    print(result['corrected_code'])
    
    for fix in result['suggested_fixes']:
        print(f"\nFix for line {fix['line']}:")
        print(f"  Original: {fix['original']}")
        print(f"  Fixed: {fix['fixed']}")
        print(f"  Issue: {fix['issue']}")
        print(f"  Suggestion: {fix['suggestion']}")
    
    for step in result['debug_steps']:
        print(f"Debug step: {step}")
    
    # Should provide comprehensive analysis
    assert result['valid'] == False
    assert len(result['issues']) > 0
    assert len(result['suggested_fixes']) > 0
    assert '"/route"' in result['corrected_code']
    print("PASS: debug_mermaid tool working correctly\n")

def test_corrected_code():
    """Test that the corrected code actually validates."""
    print("=== Testing Corrected Code Validation ===")
    
    debug_result = debug_mermaid(ORIGINAL_BROKEN_MARKDOWN)
    corrected_code = debug_result['corrected_code']
    
    validation_result = validate_obsidian_markdown(corrected_code, packs=['mermaid'])
    
    print(f"Original code valid: {debug_result['valid']}")
    print(f"Corrected code valid: {validation_result['valid']}")
    
    if not validation_result['valid']:
        print("Remaining issues:")
        for issue in validation_result['issues']:
            print(f"  - Line {issue['line']}: {issue['message']}")
    else:
        print("PASS: Corrected code validates successfully")
    
    # The corrected code should now be valid
    assert validation_result['valid'] == True
    print("PASS: Code correction working correctly\n")

if __name__ == "__main__":
    print("Testing obsidian-spec-mcp debugging tools with original error case\n")
    
    try:
        test_error_pattern_detection()
        test_enhanced_validation()
        test_debug_mermaid()
        test_corrected_code()
        
        print("SUCCESS: All tests passed! The debugging tools are working correctly.")
        print("\nSummary of improvements:")
        print("- Error pattern detection automatically suggests the right tool")
        print("- Enhanced validation provides specific fix suggestions")
        print("- debug_mermaid provides comprehensive analysis and corrected code")
        print("- Original error 'D{/route}' is correctly fixed to 'D{\"/route\"}'")
        
    except Exception as e:
        print(f"FAILED: Test failed: {e}")
        sys.exit(1)
