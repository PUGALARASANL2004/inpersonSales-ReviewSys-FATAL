"""
Comprehensive validation script for V2 Scoring System.
Tests all components and verifies system readiness.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Get project root (parent of scripts directory)
_SCRIPT_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "scripts" else _SCRIPT_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Track validation results."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures: List[Tuple[str, str]] = []
    
    def record_pass(self, test_name: str):
        self.tests_run += 1
        self.tests_passed += 1
        logger.info(f"✓ {test_name}")
    
    def record_fail(self, test_name: str, error: str):
        self.tests_run += 1
        self.tests_failed += 1
        self.failures.append((test_name, error))
        logger.error(f"✗ {test_name}: {error}")
    
    def print_summary(self):
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ✓")
        print(f"Failed: {self.tests_failed} ✗")
        
        if self.tests_failed > 0:
            print("\n" + "-" * 80)
            print("FAILURES:")
            print("-" * 80)
            for test_name, error in self.failures:
                print(f"\n{test_name}:")
                print(f"  {error}")
        
        print("\n" + "=" * 80)
        if self.tests_failed == 0:
            print("✓ ALL TESTS PASSED - SYSTEM READY")
        else:
            print(f"✗ {self.tests_failed} TEST(S) FAILED - REVIEW REQUIRED")
        print("=" * 80)
        
        return self.tests_failed == 0


def test_file_exists(result: ValidationResult):
    """Test that all required files exist."""
    files_to_check = [
        "api/scoring_v2.py",
        "api/empire_rubric_v2.yaml",
        "fuel-docs/Empire/empire_extracted_data.json",
        "test_scoring_v2.py",
        "requirements_v2.txt",
        "SCORING_V2_GUIDE.md",
        "README_V2_MIGRATION.md",
        "SCORING_QUICK_REFERENCE.md",
        "V2_IMPLEMENTATION_SUMMARY.md",
        "TESTING_CHECKLIST.md",
        "examples/score_single_call.py",
        "examples/compare_v1_v2.py",
    ]
    
    for file_path in files_to_check:
        full_path = _PROJECT_ROOT / file_path
        if full_path.exists():
            result.record_pass(f"File exists: {file_path}")
        else:
            result.record_fail(f"File exists: {file_path}", "File not found")


def test_imports(result: ValidationResult):
    """Test that all modules can be imported."""
    try:
        from api.scoring_v2 import (
            load_rubric_v2,
            load_project_reckoner,
            score_transcript_main
        )
        result.record_pass("Import: api.scoring_v2")
    except Exception as e:
        result.record_fail("Import: api.scoring_v2", str(e))


def test_load_rubric(result: ValidationResult):
    """Test loading the rubric."""
    try:
        from api.scoring_v2 import load_rubric_v2
        
        rubric = load_rubric_v2()
        
        if rubric is None:
            result.record_fail("Load rubric", "Rubric is None")
            return
        
        # Check structure
        if rubric.get('title') != "Empire Pre-Sales Call Quality Audit":
            result.record_fail("Load rubric", f"Wrong title: {rubric.get('title')}")
            return
        
        if rubric.get('total_points') != 100:
            result.record_fail("Load rubric", f"Wrong total points: {rubric.get('total_points')}")
            return
        
        categories = rubric.get('categories', [])
        if len(categories) != 5:
            result.record_fail("Load rubric", f"Wrong number of categories: {len(categories)}")
            return
        
        # Count parameters
        total_params = sum(len(cat.get('sub_parameters', [])) for cat in categories)
        if total_params != 18:
            result.record_fail("Load rubric", f"Wrong number of parameters: {total_params}")
            return
        
        result.record_pass("Load rubric")
        
    except Exception as e:
        result.record_fail("Load rubric", str(e))


def test_load_reckoner(result: ValidationResult):
    """Test loading the Ready Reckoner."""
    try:
        from api.scoring_v2 import load_project_reckoner
        
        reckoner = load_project_reckoner()
        
        if reckoner is None or not reckoner:
            result.record_fail("Load Ready Reckoner", "Reckoner is empty")
            return
        
        if 'sheets' not in reckoner:
            result.record_fail("Load Ready Reckoner", "Missing 'sheets' key")
            return
        
        result.record_pass("Load Ready Reckoner")
        
    except Exception as e:
        result.record_fail("Load Ready Reckoner", str(e))


def test_rubric_alignment(result: ValidationResult):
    """Test rubric alignment with Audit Sheet."""
    try:
        from api.scoring_v2 import load_rubric_v2
        
        rubric = load_rubric_v2()
        categories = rubric.get('categories', [])
        
        # Expected structure from Audit Sheet-001
        expected = {
            'greeting': 9,
            'project_knowledge': 48,
            'process_knowledge': 10,
            'soft_skills': 28,
            'closing': 4
        }
        
        for cat in categories:
            cat_id = cat.get('id')
            cat_max = cat.get('max_points')
            expected_max = expected.get(cat_id)
            
            if expected_max is None:
                result.record_fail(
                    f"Rubric alignment: {cat_id}",
                    f"Unexpected category"
                )
                continue
            
            if cat_max != expected_max:
                result.record_fail(
                    f"Rubric alignment: {cat_id}",
                    f"Wrong max points: {cat_max} (expected {expected_max})"
                )
                continue
            
            result.record_pass(f"Rubric alignment: {cat_id} ({cat_max} points)")
        
    except Exception as e:
        result.record_fail("Rubric alignment", str(e))


def test_scoring_demo(result: ValidationResult):
    """Test scoring with a demo transcript."""
    try:
        from api.scoring_v2 import score_transcript_main
        
        # Simple demo transcript
        demo_transcript = {
            "transcription": """
Agent: Good morning sir. This is Uma from Adityaram Property. We received your enquiry for Adityaram Empire project in Kelambakkam. Am I speaking to Mr. Ramesh?
Customer: Yes.
Agent: Thank you sir. The project is located in Kelambakkam, OMR. Plot sizes range from 650 to 3777 square feet. Pricing is Rs. 6000 per square foot. Can I know your budget requirement?
Customer: Around 50 lakhs.
Agent: Great sir. Can you visit this weekend?
Customer: Yes, Sunday is good.
Agent: Perfect. I'll share the details on WhatsApp. Thank you for choosing Adityaram Property. Have a great day!
            """,
            "speaker_segments": []
        }
        
        report = score_transcript_main(demo_transcript)
        
        # Validate report structure
        if 'summary' not in report:
            result.record_fail("Scoring demo", "Missing 'summary' in report")
            return
        
        if 'category_scores' not in report:
            result.record_fail("Scoring demo", "Missing 'category_scores' in report")
            return
        
        if 'detailed_scores' not in report:
            result.record_fail("Scoring demo", "Missing 'detailed_scores' in report")
            return
        
        summary = report['summary']
        total_score = summary.get('total_score', 0)
        total_possible = summary.get('total_possible', 0)
        
        if total_possible != 100:
            result.record_fail("Scoring demo", f"Wrong total possible: {total_possible}")
            return
        
        if total_score < 0 or total_score > 100:
            result.record_fail("Scoring demo", f"Score out of range: {total_score}")
            return
        
        # Validate all parameters have scores
        for param in report['detailed_scores']:
            score = param.get('score')
            max_points = param.get('max_points')
            
            if score < 0 or score > max_points:
                result.record_fail(
                    "Scoring demo",
                    f"{param['name']}: score {score} out of range [0, {max_points}]"
                )
                return
        
        result.record_pass(f"Scoring demo (score: {total_score}/100)")
        
    except Exception as e:
        result.record_fail("Scoring demo", str(e))


def test_evidence_format(result: ValidationResult):
    """Test that evidence includes timestamps."""
    try:
        from api.scoring_v2 import score_transcript_main
        
        demo_transcript = {
            "transcription": "Agent: Good morning. This is Uma from Adityaram Property.",
            "speaker_segments": [
                {
                    "speaker": "Agent",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "text": "Good morning. This is Uma from Adityaram Property."
                }
            ]
        }
        
        report = score_transcript_main(demo_transcript)
        
        # Check if at least some evidence has timestamps
        has_timestamps = False
        for param in report['detailed_scores']:
            evidence = param.get('evidence', [])
            for ev in evidence:
                if '[' in ev and ']' in ev:
                    has_timestamps = True
                    break
            if has_timestamps:
                break
        
        if has_timestamps:
            result.record_pass("Evidence format (includes timestamps)")
        else:
            result.record_fail("Evidence format", "No timestamps found in evidence")
        
    except Exception as e:
        result.record_fail("Evidence format", str(e))


def test_project_knowledge_validation(result: ValidationResult):
    """Test that project knowledge validation is strict."""
    try:
        from api.scoring_v2 import score_transcript_main
        
        # Transcript with WRONG pricing (should get 0 for project_knowledge_accuracy)
        wrong_pricing_transcript = {
            "transcription": """
Agent: Good morning. This is Uma from Adityaram Property. We have Adityaram Empire project in Kelambakkam. The pricing is Rs. 5500 per square foot. Plot sizes start from 650 square feet.
            """,
            "speaker_segments": []
        }
        
        report = score_transcript_main(wrong_pricing_transcript)
        
        # Find project_knowledge_accuracy parameter
        project_knowledge_score = None
        for param in report['detailed_scores']:
            if param['id'] == 'project_knowledge_accuracy':
                project_knowledge_score = param['score']
                break
        
        if project_knowledge_score is None:
            result.record_fail("Project knowledge validation", "Parameter not found")
            return
        
        # Should be 0 or very low due to wrong pricing
        if project_knowledge_score <= 3:  # Allow some tolerance
            result.record_pass("Project knowledge validation (detects wrong pricing)")
        else:
            result.record_fail(
                "Project knowledge validation",
                f"Did not detect wrong pricing (score: {project_knowledge_score})"
            )
        
    except Exception as e:
        result.record_fail("Project knowledge validation", str(e))


def main():
    """Run all validation tests."""
    print("=" * 80)
    print("V2 SCORING SYSTEM VALIDATION")
    print("=" * 80)
    print()
    
    result = ValidationResult()
    
    print("Testing file existence...")
    test_file_exists(result)
    print()
    
    print("Testing imports...")
    test_imports(result)
    print()
    
    print("Testing rubric loading...")
    test_load_rubric(result)
    print()
    
    print("Testing Ready Reckoner loading...")
    test_load_reckoner(result)
    print()
    
    print("Testing rubric alignment with Audit Sheet...")
    test_rubric_alignment(result)
    print()
    
    print("Testing scoring with demo transcript...")
    test_scoring_demo(result)
    print()
    
    print("Testing evidence format...")
    test_evidence_format(result)
    print()
    
    print("Testing project knowledge validation...")
    test_project_knowledge_validation(result)
    print()
    
    # Print summary
    success = result.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

