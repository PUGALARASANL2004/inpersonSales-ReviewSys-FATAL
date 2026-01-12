#!/usr/bin/env python3
"""
Extract all project knowledge (Empire and HappiNest) and combine into a single JSON file.
This script reads source files from both projects and saves the combined extracted content.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import numpy as np

def extract_pdf_text(pdf_path):
    """Extract text content from PDF file"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                text_content.append({
                    "page": page_num,
                    "text": text
                })
        return {"status": "success", "pages": text_content, "total_pages": len(text_content)}
    except ImportError:
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text_content = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    text_content.append({
                        "page": page_num,
                        "text": text or ""
                    })
            return {"status": "success", "pages": text_content, "total_pages": len(text_content)}
        except ImportError:
            return {"status": "error", "message": "PyPDF2 or pdfplumber not installed. Install with: pip install PyPDF2 pdfplumber"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    """Main extraction function - extracts both Empire and HappiNest"""
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == "scripts" else script_dir
    fuel_docs_dir = project_root / "fuel-docs"
    
    combined_output = {
        "extraction_date": datetime.now().isoformat(),
        "projects": {
            "Empire": {"files": {}},
            "HappiNest": {"files": {}}
        }
    }
    
    # ========== EXTRACT EMPIRE DATA ==========
    print("=" * 80)
    print("EXTRACTING EMPIRE PROJECT DATA")
    print("=" * 80)
    empire_dir = fuel_docs_dir / "Empire"
    
    # Extract PDF (Calling Script)
    pdf_path = empire_dir / "Empire-Calling Script.pdf"
    print(f"\nExtracting PDF: {pdf_path}")
    if pdf_path.exists():
        pdf_data = extract_pdf_text(pdf_path)
        combined_output["projects"]["Empire"]["files"]["calling_script_pdf"] = pdf_data
        if pdf_data["status"] == "success":
            print(f"  ✓ Extracted {pdf_data['total_pages']} pages")
        else:
            print(f"  ✗ Error: {pdf_data.get('message', 'Unknown error')}")
    else:
        print(f"  ✗ File not found: {pdf_path}")
        combined_output["projects"]["Empire"]["files"]["calling_script_pdf"] = {"status": "error", "message": "File not found"}
    
    # Extract Empire Excel files
    empire_excel_files = [
        ("scoring_excel", empire_dir / "Emprie call Scorings.xlsx"),
        ("reckoner_excel", empire_dir / "Ready Reckoner-Empire.xlsx")
    ]
    
    for file_key, excel_path in empire_excel_files:
        print(f"\nExtracting Excel: {excel_path}")
        if excel_path.exists():
            excel_data = extract_excel_data(excel_path)
            combined_output["projects"]["Empire"]["files"][file_key] = excel_data
            if excel_data["status"] == "success":
                print(f"  ✓ Extracted {len(excel_data['sheet_names'])} sheet(s): {', '.join(excel_data['sheet_names'])}")
                for sheet_name in excel_data["sheet_names"]:
                    shape = excel_data["sheets"][sheet_name]["shape"]
                    print(f"    - {sheet_name}: {shape['rows']} rows × {shape['columns']} columns")
            else:
                print(f"  ✗ Error: {excel_data.get('message', 'Unknown error')}")
        else:
            print(f"  ✗ File not found: {excel_path}")
            combined_output["projects"]["Empire"]["files"][file_key] = {"status": "error", "message": "File not found"}
    
    # ========== EXTRACT HAPPINEST DATA ==========
    print("\n" + "=" * 80)
    print("EXTRACTING HAPPINEST PROJECT DATA")
    print("=" * 80)
    
    # Check for HappiNest directory or file in Empire folder
    happinest_dir = fuel_docs_dir / "HappiNest"
    happinest_file_patterns = [
        ("HappiNest", happinest_dir / "AdithyaRam_ReadyReckoner-HappiNestProject.xlsm"),
        ("HappiNest", empire_dir / "AdithyaRam_ReadyReckoner-HappiNestProject.xlsm"),
        ("HappiNest", fuel_docs_dir / "AdithyaRam_ReadyReckoner-HappiNestProject.xlsm"),
    ]
    
    happinest_excel_found = False
    for label, excel_path in happinest_file_patterns:
        if excel_path.exists():
            print(f"\nExtracting HappiNest Excel: {excel_path}")
            excel_data = extract_excel_data(excel_path)
            combined_output["projects"]["HappiNest"]["files"]["reckoner_excel"] = excel_data
            if excel_data["status"] == "success":
                print(f"  ✓ Extracted {len(excel_data['sheet_names'])} sheet(s): {', '.join(excel_data['sheet_names'])}")
                for sheet_name in excel_data["sheet_names"]:
                    shape = excel_data["sheets"][sheet_name]["shape"]
                    print(f"    - {sheet_name}: {shape['rows']} rows × {shape['columns']} columns")
                happinest_excel_found = True
                break
            else:
                print(f"  ✗ Error: {excel_data.get('message', 'Unknown error')}")
    
    if not happinest_excel_found:
        print(f"\n  ⚠ Warning: HappiNest Excel file not found. Searched in:")
        for label, path in happinest_file_patterns:
            print(f"    - {path}")
        combined_output["projects"]["HappiNest"]["files"]["reckoner_excel"] = {"status": "error", "message": "File not found in any expected location"}
    
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
    
    # Save combined JSON file (in fuel-docs directory)
    output_file = fuel_docs_dir / "project_knowledge.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined_output, f, indent=2, ensure_ascii=False, cls=JSONEncoder)
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"\n✓ Combined project knowledge saved to: {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024:.2f} KB")
    print(f"\nThis file contains data for:")
    print(f"  - Empire: {len(combined_output['projects']['Empire']['files'])} files")
    print(f"  - HappiNest: {len(combined_output['projects']['HappiNest']['files'])} files")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()

