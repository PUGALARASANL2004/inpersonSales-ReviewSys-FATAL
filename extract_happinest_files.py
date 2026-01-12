#!/usr/bin/env python3
"""
Extract HappiNest scoring rules from Excel files.
This script reads the Ready Reckoner Excel file,
then saves the extracted content in a readable JSON format.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import numpy as np

def extract_excel_data(excel_path):
    """Extract all data from Excel file"""
    try:
        excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
        sheets_data = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')
            
            # Convert datetime columns to strings for JSON serialization
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Replace NaN and NaT with empty strings
            df = df.fillna("")
            
            # Convert DataFrame to multiple formats for readability
            sheets_data[sheet_name] = {
                "columns": df.columns.tolist(),
                "shape": {"rows": len(df), "columns": len(df.columns)},
                "data": df.to_dict('records'),  # Already has NaN/NaT replaced
                "text_table": df.to_string(),  # Plain text table format
                "csv_format": df.to_csv(index=False)  # CSV format for easy reading
            }
        
        return {"status": "success", "sheets": sheets_data, "sheet_names": excel_file.sheet_names}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    """Main extraction function"""
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == "scripts" else script_dir
    base_dir = project_root / "fuel-docs/HappiNest"
    
    output = {
        "extraction_date": datetime.now().isoformat(),
        "files": {}
    }
    
    # Extract Excel files
    excel_files = [
        ("reckoner_excel", base_dir / "AdithyaRam_ReadyReckoner-HappiNestProject.xlsm")
    ]
    
    for file_key, excel_path in excel_files:
        print(f"\nExtracting Excel: {excel_path}")
        if excel_path.exists():
            excel_data = extract_excel_data(excel_path)
            output["files"][file_key] = excel_data
            if excel_data["status"] == "success":
                print(f"  ✓ Extracted {len(excel_data['sheet_names'])} sheet(s): {', '.join(excel_data['sheet_names'])}")
                for sheet_name in excel_data["sheet_names"]:
                    shape = excel_data["sheets"][sheet_name]["shape"]
                    print(f"    - {sheet_name}: {shape['rows']} rows × {shape['columns']} columns")
            else:
                print(f"  ✗ Error: {excel_data.get('message', 'Unknown error')}")
        else:
            print(f"  ✗ File not found: {excel_path}")
            output["files"][file_key] = {"status": "error", "message": "File not found"}
    
    # Custom JSON encoder to handle special types
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime, pd.Timestamp)):
                return obj.isoformat()
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif pd.isna(obj):
                return None
            return super().default(obj)
    
    # Save to JSON file
    output_file = base_dir / "happinest_extracted_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=JSONEncoder)
    
    print(f"\n✓ Extraction complete! Data saved to: {output_file}")
    print(f"\nFile size: {output_file.stat().st_size / 1024:.2f} KB")
    
    # Also create a human-readable text summary
    summary_file = base_dir / "happinest_extracted_summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("HAPPINEST FILES EXTRACTION SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Extraction Date: {output['extraction_date']}\n\n")
        
        # Excel Summaries
        for file_key, excel_path in excel_files:
            file_label = file_key.replace("_", " ").title()
            f.write(f"\n{file_label.upper()}\n")
            f.write("-" * 80 + "\n")
            if file_key in output["files"]:
                excel_info = output["files"][file_key]
                if excel_info["status"] == "success":
                    for sheet_name in excel_info["sheet_names"]:
                        f.write(f"\nSheet: {sheet_name}\n")
                        f.write(excel_info["sheets"][sheet_name]["text_table"])
                        f.write("\n\n")
                else:
                    f.write(f"Error: {excel_info.get('message', 'Unknown')}\n\n")
        
        f.write("=" * 80 + "\n")
    
    print(f"✓ Human-readable summary saved to: {summary_file}")
    print(f"\nPlease share both files with the AI assistant for rubric creation.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()

