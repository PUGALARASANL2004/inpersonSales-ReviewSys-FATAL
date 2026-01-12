"""
Example: Score a single call transcript using V2 system.

This demonstrates the simplest way to use the scoring system.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path to import api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.scoring_v2 import score_transcript_main


def score_call_from_file(transcript_path: str, output_path: str = None):
    """
    Score a call transcript from a text file.
    
    Args:
        transcript_path: Path to transcript text file
        output_path: Optional path to save JSON report
    """
    print(f"Loading transcript from: {transcript_path}")
    
    # Load transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    # Prepare data
    transcript_data = {
        "transcription": transcript_text,
        "speaker_segments": []  # Add if available
    }
    
    print("Scoring transcript...")
    
    # Score the transcript
    result = score_transcript_main(transcript_data)
    
    # Print summary
    summary = result['summary']
    print("\n" + "=" * 60)
    print("SCORING RESULTS")
    print("=" * 60)
    print(f"Total Score: {summary['total_score']}/{summary['total_possible']}")
    print(f"Percentage: {summary['percentage']}%")
    print(f"Grade: {get_grade(summary['percentage'])}")
    
    # Print category breakdown
    print("\n" + "-" * 60)
    print("CATEGORY BREAKDOWN")
    print("-" * 60)
    for cat_id, cat_data in result['category_scores'].items():
        print(f"{cat_data['name']:.<40} {cat_data['score']:>3}/{cat_data['max_points']:<3} ({cat_data['percentage']:>5.1f}%)")
    
    # Print top 3 strengths and weaknesses
    print("\n" + "-" * 60)
    print("TOP STRENGTHS")
    print("-" * 60)
    strengths = sorted(
        result['detailed_scores'],
        key=lambda x: x['percentage'],
        reverse=True
    )[:3]
    for i, param in enumerate(strengths, 1):
        print(f"{i}. {param['name']}: {param['score']}/{param['max_points']} ({param['percentage']:.1f}%)")
    
    print("\n" + "-" * 60)
    print("TOP IMPROVEMENT AREAS")
    print("-" * 60)
    weaknesses = sorted(
        result['detailed_scores'],
        key=lambda x: x['percentage']
    )[:3]
    for i, param in enumerate(weaknesses, 1):
        print(f"{i}. {param['name']}: {param['score']}/{param['max_points']} ({param['percentage']:.1f}%)")
        print(f"   Issue: {param['rationale'][:100]}...")
    
    # Save report if output path provided
    if output_path:
        print(f"\nSaving detailed report to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("Report saved successfully!")
    
    return result


def get_grade(percentage: float) -> str:
    """Convert percentage to letter grade."""
    if percentage >= 90:
        return "A+ (Excellent)"
    elif percentage >= 80:
        return "A (Very Good)"
    elif percentage >= 70:
        return "B (Good)"
    elif percentage >= 60:
        return "C (Adequate)"
    elif percentage >= 50:
        return "D (Below Standard)"
    else:
        return "F (Poor)"


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python score_single_call.py <transcript_file> [output_file]")
        print("\nExample:")
        print("  python score_single_call.py transcript.txt")
        print("  python score_single_call.py transcript.txt report.json")
        sys.exit(1)
    
    transcript_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(transcript_path).exists():
        print(f"Error: Transcript file not found: {transcript_path}")
        sys.exit(1)
    
    try:
        score_call_from_file(transcript_path, output_path)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

