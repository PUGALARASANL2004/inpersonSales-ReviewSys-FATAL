"""
Example: Compare V1 and V2 scoring systems side-by-side.

This helps understand the differences between binary and granular scoring.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.scoring import score_transcript as score_v1
from api.scoring_v2 import score_transcript_main as score_v2


def compare_scoring_systems(transcript_path: str):
    """
    Compare V1 and V2 scoring on the same transcript.
    
    Args:
        transcript_path: Path to transcript file
    """
    print(f"Loading transcript from: {transcript_path}")
    
    # Load transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    transcript_data = {
        "transcription": transcript_text,
        "speaker_segments": []
    }
    
    print("\n" + "=" * 80)
    print("SCORING COMPARISON: V1 (Binary) vs V2 (Granular)")
    print("=" * 80)
    
    # Score with V1
    print("\nScoring with V1 (Binary System)...")
    try:
        result_v1 = score_v1(transcript_data, rubric_path="api/empire_rubric.yaml")
        v1_success = True
    except Exception as e:
        print(f"V1 Scoring failed: {e}")
        v1_success = False
    
    # Score with V2
    print("Scoring with V2 (Granular System)...")
    try:
        result_v2 = score_v2(transcript_data, rubric_path="api/empire_rubric_v2.yaml")
        v2_success = True
    except Exception as e:
        print(f"V2 Scoring failed: {e}")
        v2_success = False
    
    if not v1_success and not v2_success:
        print("Both scoring systems failed!")
        return
    
    # Compare overall scores
    print("\n" + "-" * 80)
    print("OVERALL SCORES")
    print("-" * 80)
    
    if v1_success:
        print(f"V1 (Binary):   {result_v1['total_score']}/{result_v1['total_points']} ({result_v1['percentage']}%)")
    if v2_success:
        print(f"V2 (Granular): {result_v2['summary']['total_score']}/{result_v2['summary']['total_possible']} ({result_v2['summary']['percentage']}%)")
    
    if v1_success and v2_success:
        diff = result_v2['summary']['percentage'] - result_v1['percentage']
        print(f"Difference:    {diff:+.2f}% (V2 - V1)")
    
    # Compare parameter by parameter
    if v1_success and v2_success:
        print("\n" + "-" * 80)
        print("PARAMETER COMPARISON")
        print("-" * 80)
        print(f"{'Parameter':<40} {'V1 Score':<12} {'V2 Score':<12} {'Diff':<8}")
        print("-" * 80)
        
        # Create lookup for V2 scores
        v2_scores = {p['id']: p for p in result_v2['detailed_scores']}
        
        for criterion in result_v1['criteria_scores']:
            param_id = criterion['id']
            v1_score = criterion['points_awarded']
            v1_max = criterion['max_points']
            v1_pct = (v1_score / v1_max * 100) if v1_max > 0 else 0
            
            # Find corresponding V2 parameter
            v2_param = v2_scores.get(param_id)
            if v2_param:
                v2_score = v2_param['score']
                v2_max = v2_param['max_points']
                v2_pct = v2_param['percentage']
                
                diff = v2_pct - v1_pct
                diff_str = f"{diff:+.1f}%"
                
                print(f"{criterion['name']:<40} {v1_score}/{v1_max} ({v1_pct:.0f}%){'':<3} {v2_score}/{v2_max} ({v2_pct:.0f}%){'':<3} {diff_str:<8}")
        
        # Analyze differences
        print("\n" + "-" * 80)
        print("ANALYSIS")
        print("-" * 80)
        
        # Count parameters with significant differences
        significant_diffs = []
        for criterion in result_v1['criteria_scores']:
            param_id = criterion['id']
            v1_pct = (criterion['points_awarded'] / criterion['max_points'] * 100) if criterion['max_points'] > 0 else 0
            v2_param = v2_scores.get(param_id)
            if v2_param:
                v2_pct = v2_param['percentage']
                diff = abs(v2_pct - v1_pct)
                if diff >= 20:  # 20% or more difference
                    significant_diffs.append({
                        'name': criterion['name'],
                        'v1_pct': v1_pct,
                        'v2_pct': v2_pct,
                        'diff': v2_pct - v1_pct
                    })
        
        if significant_diffs:
            print(f"\nParameters with significant differences (≥20%):")
            for item in sorted(significant_diffs, key=lambda x: abs(x['diff']), reverse=True):
                print(f"  • {item['name']}")
                print(f"    V1: {item['v1_pct']:.0f}% → V2: {item['v2_pct']:.0f}% (Δ {item['diff']:+.0f}%)")
        else:
            print("\nNo parameters with significant differences (≥20%).")
        
        # V2 advantages
        print("\n" + "-" * 80)
        print("V2 ADVANTAGES")
        print("-" * 80)
        print("✓ Granular scoring (0 to max) provides more nuanced assessment")
        print("✓ Evidence with exact timestamps for every score")
        print("✓ Comprehensive rationale explaining each decision")
        print("✓ Strict project knowledge validation against Ready Reckoner")
        print("✓ Organized by categories for better understanding")
        print("✓ Partial credit for partial execution")
        print("✓ Less prone to hallucination (evidence-required)")
    
    print("\n" + "=" * 80)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python compare_v1_v2.py <transcript_file>")
        print("\nExample:")
        print("  python compare_v1_v2.py transcript.txt")
        sys.exit(1)
    
    transcript_path = sys.argv[1]
    
    if not Path(transcript_path).exists():
        print(f"Error: Transcript file not found: {transcript_path}")
        sys.exit(1)
    
    try:
        compare_scoring_systems(transcript_path)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

