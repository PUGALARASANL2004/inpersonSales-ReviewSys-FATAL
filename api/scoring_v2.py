"""
Advanced transcript scoring system with evidence-based granular evaluation.
Version 2.0 - Complete rewrite for Empire project scoring.

Key features:
- Granular scoring (0 to max points, not just binary)
- Evidence-based evaluation with timestamps
- Project knowledge validation against Ready Reckoner
- Calling script adherence validation
- No hallucination - every score must be justified with evidence
- Advanced prompt engineering for accurate assessment
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL, AZURE_ENDPOINT

logger = logging.getLogger(__name__)


def load_rubric_v2(rubric_path: str = None) -> Dict[str, Any]:
    """Load the version 2 rubric YAML file."""
    if rubric_path is None:
        # Default to empire_rubric_v2.yaml
        rubric_file = Path(__file__).parent / "empire_rubric_v2.yaml"
    else:
        rubric_file = Path(rubric_path)
        if not rubric_file.exists() and not rubric_file.is_absolute():
            rubric_file = Path(__file__).parent / rubric_path
            if not rubric_file.exists():
                rubric_file = Path(__file__).parent.parent / rubric_path
    
    if not rubric_file.exists():
        raise FileNotFoundError(f"Rubric file not found: {rubric_path or 'empire_rubric_v2.yaml'}")
    
    logger.info(f"Loading rubric v2 from: {rubric_file}")
    try:
        with open(rubric_file, 'r', encoding='utf-8') as f:
            rubric = yaml.safe_load(f)
        if rubric is None:
            raise ValueError("Rubric file is empty or contains no valid YAML")
        return rubric
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {rubric_file}: {e}")
        raise ValueError(f"Failed to parse rubric YAML file: {e}") from e


def load_project_reckoner() -> Dict[str, Any]:
    """Load project Ready Reckoner data from combined JSON for both Empire and HappiNest."""
    base_path = Path(__file__).parent.parent / "fuel-docs"
    
    # Try loading from combined knowledge file first
    combined_file = base_path / "project_knowledge.json"
    if combined_file.exists():
        logger.info(f"Loading combined project knowledge from: {combined_file}")
        try:
            with open(combined_file, 'r', encoding='utf-8') as f:
                combined_data = json.load(f)
                
            # Convert new format to old format for backward compatibility
            if "projects" in combined_data:
                converted_data = {
                    "extraction_date": combined_data.get("extraction_date", ""),
                    "files": {}
                }
                
                # Convert Empire data
                if "Empire" in combined_data["projects"]:
                    empire_files = combined_data["projects"]["Empire"].get("files", {})
                    for key, value in empire_files.items():
                        converted_data["files"][f"empire_{key}"] = value
                
                # Convert HappiNest data
                if "HappiNest" in combined_data["projects"]:
                    happinest_files = combined_data["projects"]["HappiNest"].get("files", {})
                    for key, value in happinest_files.items():
                        converted_data["files"][f"happinest_{key}"] = value
                
                logger.info(f"Loaded Ready Reckoner data for both projects")
                return converted_data
        except Exception as e:
            logger.warning(f"Error loading combined knowledge file: {e}")
    
    # Fallback to separate files for backward compatibility
    combined_data = {
        "extraction_date": "",
        "files": {}
    }
    
    # Load Empire data
    empire_file = base_path / "Empire" / "empire_extracted_data.json"
    if empire_file.exists():
        logger.info(f"Loading Empire Ready Reckoner from: {empire_file}")
        try:
            with open(empire_file, 'r', encoding='utf-8') as f:
                empire_data = json.load(f)
                if "files" in empire_data:
                    # Prefix keys with "empire_" to avoid conflicts
                    for key, value in empire_data["files"].items():
                        combined_data["files"][f"empire_{key}"] = value
                if "extraction_date" in empire_data:
                    combined_data["extraction_date"] = empire_data.get("extraction_date", "")
        except Exception as e:
            logger.warning(f"Error loading Empire data: {e}")
    else:
        logger.warning(f"Empire Ready Reckoner file not found: {empire_file}")
    
    # Load HappiNest data
    happinest_file = base_path / "HappiNest" / "happinest_extracted_data.json"
    if not happinest_file.exists():
        # Also check Empire folder as fallback
        happinest_file = base_path / "Empire" / "happinest_extracted_data.json"
    
    if happinest_file.exists():
        logger.info(f"Loading HappiNest Ready Reckoner from: {happinest_file}")
        try:
            with open(happinest_file, 'r', encoding='utf-8') as f:
                happinest_data = json.load(f)
                if "files" in happinest_data:
                    # Prefix keys with "happinest_" to avoid conflicts
                    for key, value in happinest_data["files"].items():
                        combined_data["files"][f"happinest_{key}"] = value
        except Exception as e:
            logger.warning(f"Error loading HappiNest data: {e}")
    else:
        logger.warning(f"HappiNest Ready Reckoner file not found")
    
    logger.info(f"Loaded Ready Reckoner data for both projects")
    return combined_data


def load_faq_data() -> Dict[str, Any]:
    """Load FAQ data from JSON file for both Empire and HappiNest."""
    base_path = Path(__file__).parent.parent / "fuel-docs"
    
    combined_data = {}
    
    # Load Empire FAQ data
    empire_faq_file = base_path / "Empire" / "empire_faq_data.json"
    if empire_faq_file.exists():
        logger.info(f"Loading Empire FAQ data from: {empire_faq_file}")
        try:
            with open(empire_faq_file, 'r', encoding='utf-8') as f:
                empire_faq = json.load(f)
                if isinstance(empire_faq, dict):
                    # Prefix keys with "empire_" to avoid conflicts
                    for key, value in empire_faq.items():
                        combined_data[f"empire_{key}"] = value
                else:
                    combined_data["empire_faq"] = empire_faq
        except Exception as e:
            logger.warning(f"Error loading Empire FAQ data: {e}")
    else:
        logger.warning(f"Empire FAQ file not found: {empire_faq_file}")
    
    # Load HappiNest FAQ data
    happinest_faq_file = base_path / "HappiNest" / "happinest_faq_data.json"
    if happinest_faq_file.exists():
        logger.info(f"Loading HappiNest FAQ data from: {happinest_faq_file}")
        try:
            with open(happinest_faq_file, 'r', encoding='utf-8') as f:
                happinest_faq = json.load(f)
                if isinstance(happinest_faq, dict):
                    # Prefix keys with "happinest_" to avoid conflicts
                    for key, value in happinest_faq.items():
                        combined_data[f"happinest_{key}"] = value
                else:
                    combined_data["happinest_faq"] = happinest_faq
        except Exception as e:
            logger.warning(f"Error loading HappiNest FAQ data: {e}")
    else:
        logger.warning(f"HappiNest FAQ file not found: {happinest_faq_file}")
    
    logger.info(f"Loaded FAQ data for both projects")
    return combined_data


def load_calling_script() -> str:
    """Load the calling script reference text."""
    script_text = """
# ADITYARAM EMPIRE PRE-SALES CALLING SCRIPT

**Executive:** Good Morning sir / madam

This is (Uma) from Adityaram Property, one of the leading Real Estate developer in South India. We have received your enquiry for Adityaram Empire project, plot property in Kelambakkam, OMR

Am I speaking to Mr Customer Name

**Customer:** Yes

**Executive:** Thanks for confirmation sir/madam

Adityaram Empire project is located in OMR, Kelambakkam, (Pudupakkam) location

When you are travelling from Kelambakkam to Vandalur road, within 1.5 kms, you can find Rajinikanth sir farm house on your left hand side. There you need to take left and in the same road within 900 mts, you can find our project on your left.

Totally Adityaram Empire PH 2 it is 12 acres of land extent along with 1.5 acres open park with 20+ world class amenities where we developed 268 villa plots.

We have beautiful lake view villa plot in this project.

Adjacent to our project, in 20 acres, fresh water pond is available where in future too there won't be any water scarcity issues, now within 20ft, sweet ground water is available. Also ventilation and air circulation will be in higher end.

Minimum plot area starts from 671 sq.ft. to 3777 sq.ft with price starting from 42 Lakhs

**Executive:** Can I know your actual requirement sir - Budget & size?

**Customer:** 60 L budget

**Executive:** Great sir, you can able to get plots within your desired budget.

Can you visit our project by today along with your family?

Customer: If, No...

Executive: Why don't you try to visit by tomorrow sir to grab your best plot sir.

Customer: Again If, No...

Executive: Otherwise, try to visit by this weekend (Saturday / Sunday)

Customer: If, Yes...

Executive: Can I know your alternative number and your residing location.

Customer: 91XXXX777

Executive: At what time you will be reaching our project sir?

Customer: Around 11 am

Executive: Fine, I am fixing your appointment with our sales manager to feel better experience.

As there is fast moving, please bring your cheque book or Card to block your dream villa plot.

Booking Advance amount will be One Lakh

Executive: Will share the project Detail / Location map to this WhatsApp number with Brochure. (Confirmation on WhatsApp Number)

Thank you for choosing Adityaram Property. Have a great day sir!

## Why we choose Adityaram Empire

- Location ambience is very calm & peaceful.
- We never ever face water scarcity in this location
- Upcoming metro work has been planned from Kelambakkam to Kilambakkam
- In 2019 the price was about Rs. 2,600/- per sq.ft and now the market price is Rs. 6,600/- per sq.ft.. Within 6 years, the appreciation is Rs. 5000/- per sq.ft..
- Now we are selling at Rs. 6000/- per sq.ft. Within a year period, we assure you can get 20% of appreciation.
"""
    return script_text


def extract_reckoner_facts(reckoner_data: Dict[str, Any]) -> str:
    """Extract and format Ready Reckoner facts for validation.
    Handles both Empire and HappiNest project knowledge."""
    if not reckoner_data or "files" not in reckoner_data:
        return "Ready Reckoner data not available."
    
    try:
        facts = []
        files = reckoner_data.get("files", {})
        
        # Extract Empire facts
        empire_reckoner = files.get("empire_reckoner_excel", {})
        if empire_reckoner.get("status") == "success":
            empire_sheets = empire_reckoner.get("sheets", {})
            # Try different possible sheet names for Empire
            empire_sheet = None
            for sheet_name in ["Sheet2", "Ready Reckoner"]:
                if sheet_name in empire_sheets:
                    empire_sheet = empire_sheets[sheet_name]
                    if isinstance(empire_sheet, dict):
                        empire_sheet = empire_sheet.get("data", [])
                    break
            
            if empire_sheet and len(empire_sheet) >= 2:
                # Extract headers and main data row
                headers = empire_sheet[0]
                main_row = empire_sheet[1] if len(empire_sheet) > 1 else []
                
                # Create a dictionary of the main project data
                project_data = {}
                for i, header in enumerate(headers):
                    if i < len(main_row):
                        project_data[header] = main_row[i]
                
                facts.append("=" * 80)
                facts.append("READY RECKONER - ADITYARAM EMPIRE PHASE 2")
                facts.append("Official Project Facts for Validation")
                facts.append("=" * 80)
                facts.append("")
                
                # Project Name
                project = project_data.get("Project", "").strip()
                if project:
                    facts.append(f"PROJECT NAME: {project}")
                    facts.append("  ✓ Acceptable mentions: 'Adityaram Empire', 'Empire Phase 2', 'Adityaram Empire Phase 2'")
                    facts.append("  ✗ CRITICAL ERROR: Any other project name = 0 score for project_knowledge_accuracy")
                    facts.append("")
                
                # Location
                location = project_data.get("Location", "").strip()
                if location:
                    facts.append(f"LOCATION: {location}")
                    facts.append("  ✓ Key details: Kelambakkam, OMR, 3 Kms from Kelambakkam Junction, Pudupakkam")
                    facts.append("")
                
                # Approval
                approval = project_data.get("Approval", "").strip()
                if approval:
                    facts.append(f"APPROVAL: {approval}")
                    facts.append("  ✓ Must be: DTCP & RERA Approved")
                    facts.append("  ✗ CRITICAL ERROR: Wrong approval status = 0 score")
                    facts.append("")
                
                # Pricing - CRITICAL
                rate = project_data.get("Rate per sqft", "").strip()
                if rate:
                    facts.append("PRICING (CRITICAL - STRICT VALIDATION REQUIRED):")
                    facts.append(f"  Reckoner Data: {rate}")
                    facts.append("  ✓ CORRECT VALUES:")
                    facts.append("     - Rs. 6000/- per sq.ft. (Early Bird Offer Price)")
                    facts.append("     - Rs. 6300/- per sq.ft. (Actual Price)")
                    facts.append("  ✗ CRITICAL ERROR - AUTOMATIC 0 SCORE:")
                    facts.append("     - ANY price outside Rs. 6000-6300 range")
                    facts.append("     - Examples of WRONG prices: Rs. 5500, Rs. 5000, Rs. 4500, Rs. 7000, Rs. 8000")
                    facts.append("     - Even if agent says 'starting from Rs. 5500' = WRONG = 0 score")
                    facts.append("")
                
                # Plot Sizes - CRITICAL
                plot_size = project_data.get("Actual Plot Size", "").strip()
                if plot_size:
                    facts.append("PLOT SIZES (CRITICAL - STRICT VALIDATION REQUIRED):")
                    facts.append(f"  Reckoner Data: {plot_size}")
                    facts.append("  ✓ CORRECT VALUES:")
                    facts.append("     - Minimum: 617 sq.ft. (650 sq.ft. or 671 sq.ft. also acceptable)")
                    facts.append("     - Maximum: 3777 sq.ft.")
                    facts.append("  ✗ CRITICAL ERROR - AUTOMATIC 0 SCORE:")
                    facts.append("     - Minimum plot size below 617 sq.ft.")
                    facts.append("     - Examples of WRONG minimum sizes: 500 sq.ft., 400 sq.ft., 550 sq.ft.")
                    facts.append("     - Even if agent says 'starting from 500 sq.ft.' = WRONG = 0 score")
                    facts.append("")
                
                # Price Range
                price_onwards = project_data.get("Price Onwards", "").strip()
                if price_onwards:
                    facts.append(f"PRICE RANGE: {price_onwards}")
                    facts.append("  ✓ Minimum: Rs. 42 Lakhs")
                    facts.append("  ✓ Maximum: Rs. 2.45 Crores")
                    facts.append("")
                
                # Land Extent
                land_extent = project_data.get("Land Extent", "").strip()
                if land_extent:
                    facts.append(f"LAND EXTENT: {land_extent}")
                    facts.append("  ✓ Must be: 12 Acres")
                    facts.append("")
                
                # Total Units
                total_units = project_data.get("Total Units", "").strip()
                if total_units:
                    facts.append(f"TOTAL PLOTS: {total_units}")
                    facts.append("  ✓ Phase 2: 223 plots (Total project: 268 plots)")
                    facts.append("")
                
                # Status
                status = project_data.get("Status", "").strip()
                if status:
                    facts.append(f"STATUS: {status}")
                    facts.append("  ✓ Must be: Ready to Construct")
                    facts.append("")
        
                # Bank Loan
                bank_loan = project_data.get("Bank Loan", "").strip()
                if bank_loan:
                    facts.append(f"BANK LOAN: {bank_loan}")
                    facts.append("  ✓ Up to 90% loan available")
                    facts.append("")
                
                # USPs
                usp = project_data.get("USP", "").strip()
                if usp:
                    facts.append(f"USP: {usp}")
                    facts.append("")
                
                # Features
                features = project_data.get("Product Features", "").strip()
                if features:
                    facts.append(f"PRODUCT FEATURES: {features}")
                    facts.append("")
                
                facts.append("=" * 80)
                facts.append("VALIDATION INSTRUCTIONS - EMPIRE")
                facts.append("=" * 80)
                facts.append("")
                facts.append("For Empire project:")
                facts.append("- CRITICAL ERRORS: Wrong project name, pricing outside Rs. 6000-6300 per sq.ft., minimum plot size below 617 sq.ft.")
                facts.append("")
        
        # Extract HappiNest facts
        happinest_reckoner = files.get("happinest_reckoner_excel", {})
        if happinest_reckoner.get("status") == "success":
            happinest_sheets = happinest_reckoner.get("sheets", {})
            happinest_sheet = None
            for sheet_name in happinest_sheets.keys():
                sheet_info = happinest_sheets[sheet_name]
                if isinstance(sheet_info, dict) and "data" in sheet_info:
                    happinest_data_list = sheet_info["data"]
                    if happinest_data_list and len(happinest_data_list) > 0:
                        happinest_sheet = happinest_data_list
                        break
            
            if happinest_sheet and len(happinest_sheet) > 0:
                # Get the first row which contains the main project information
                happinest_main_data = happinest_sheet[0] if isinstance(happinest_sheet[0], dict) else {}
                
                facts.append("")
                facts.append("=" * 80)
                facts.append("READY RECKONER - HAPPINEST")
                facts.append("Official Project Facts for Validation")
                facts.append("=" * 80)
                facts.append("")
                
                # Extract HappiNest project facts
                happinest_project = happinest_main_data.get("Project", "").strip()
                if happinest_project:
                    facts.append(f"PROJECT NAME: {happinest_project}")
                    facts.append("  ✓ Acceptable mentions: 'HappiNest', 'Happinest', or variations")
                    facts.append("")
                
                for key in ["Location", "Approval", "Rate per sqft", "Plot Size", "Price\nonwards", "Price onwards", 
                           "Land Extent", "Total Units", "Status", "Bank Loan", "USP", "Product Features"]:
                    value = happinest_main_data.get(key, "").strip()
                    if value:
                        facts.append(f"{key.upper().replace('_', ' ')}: {value}")
                        facts.append("")
                
                facts.append("=" * 80)
                facts.append("VALIDATION INSTRUCTIONS - HAPPINEST")
                facts.append("=" * 80)
                facts.append("")
                facts.append("For HappiNest project:")
                facts.append("- Validate against the facts listed above")
                facts.append("")
        
        # General validation instructions
        if facts:
            facts.append("")
            facts.append("=" * 80)
            facts.append("GENERAL VALIDATION INSTRUCTIONS")
            facts.append("=" * 80)
            facts.append("")
            facts.append("1. First, identify which project the agent is discussing (Empire or HappiNest)")
            facts.append("2. Extract EVERY factual statement made by agent (with timestamp)")
            facts.append("3. Compare EACH fact against the Ready Reckoner data for the specific project")
            facts.append("4. CRITICAL ERRORS that result in 0 score for project_knowledge_accuracy:")
            facts.append("   - Wrong project name")
            facts.append("   - Pricing/plot sizes that don't match project facts")
            facts.append("   - Wrong approvals or major location errors")
            facts.append("5. Even ONE critical error = 0 score for project_knowledge_accuracy")
            facts.append("6. Minor variations acceptable: rounding numbers, slight wording differences")
            facts.append("7. NOT acceptable: contradicting core facts, wrong numbers, wrong project")
            facts.append("")
        
        return "\n".join(facts) if facts else "Ready Reckoner data not available."
        
    except Exception as e:
        logger.warning(f"Error extracting reckoner facts: {e}")
        return f"Ready Reckoner data available but error in extraction: {e}"


def format_speaker_segments(segments: List[Dict[str, Any]]) -> str:
    """Format speaker segments with timestamps for prompt."""
    if not segments:
        return "Speaker segments with timestamps not available."
    
    lines = []
    lines.append("=" * 80)
    lines.append("TRANSCRIPT WITH SPEAKER SEGMENTS AND TIMESTAMPS")
    lines.append("=" * 80)
    lines.append("")
    lines.append("CRITICAL: Use these EXACT timestamps in your evidence citations.")
    lines.append("Format: [MM:SS - MM:SS] for ranges, [MM:SS] for single point")
    lines.append("")
    
    sorted_segments = sorted(segments, key=lambda s: s.get("start_time", 0.0))
    last_end = None
    
    for seg in sorted_segments:
        speaker = seg.get("speaker", "Unknown")
        start = seg.get("start_time", 0.0)
        end = seg.get("end_time", start)
        text = str(seg.get("text", "")).strip()
        
        start_str = format_time(start)
        end_str = format_time(end)
        
        # Note silences/gaps
        if last_end is not None:
            gap = max(0.0, float(start) - float(last_end))
            if gap >= 2.5:
                lines.append(f"[SILENCE: ~{gap:.1f}s gap]")
        
        lines.append(f"{speaker} [{start_str} - {end_str}]: {text}")
        last_end = end
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("")
    
    return "\n".join(lines[:300])  # Limit to avoid token overflow


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    try:
        s = float(seconds)
    except (TypeError, ValueError):
        return "0:00"
    if s < 0:
        s = 0
    minutes = int(s // 60)
    secs = int(s % 60)
    return f"{minutes}:{secs:02d}"


def extract_faq_facts(faq_data: Dict[str, Any]) -> str:
    """Extract and format FAQ facts for knowledge base validation."""
    if not faq_data:
        return "FAQ data not available."
    
    try:
        lines = []
        lines.append("=" * 80)
        lines.append("ADITYARAM EMPIRE FAQ - KNOWLEDGE BASE")
        lines.append("Frequently Asked Questions for Project Knowledge Validation")
        lines.append("=" * 80)
        lines.append("")
        lines.append("This FAQ document contains comprehensive information about Adityaram Empire project.")
        lines.append("Use this as ADDITIONAL knowledge base alongside Ready Reckoner for:")
        lines.append("  - Validating agent's responses to common customer questions")
        lines.append("  - Checking accuracy of project details, amenities, location, pricing")
        lines.append("  - Verifying information about schools, hospitals, IT hubs, connectivity")
        lines.append("  - Ensuring agent provides complete and accurate answers")
        lines.append("")
        
        # Key Highlights
        highlights = faq_data.get("key_highlights", [])
        if highlights:
            lines.append("KEY HIGHLIGHTS:")
            for i, highlight in enumerate(highlights, 1):
                lines.append(f"  {i}. {highlight}")
            lines.append("")
        
        # FAQs
        faqs = faq_data.get("faqs", [])
        if faqs:
            lines.append("FREQUENTLY ASKED QUESTIONS:")
            lines.append("")
            for i, faq in enumerate(faqs, 1):
                question = faq.get("question", "").strip()
                answer = faq.get("answer", "").strip()
                if question and answer:
                    lines.append(f"Q{i}. {question}")
                    lines.append(f"    A: {answer}")
                    lines.append("")
        
        lines.append("=" * 80)
        lines.append("FAQ VALIDATION GUIDELINES")
        lines.append("=" * 80)
        lines.append("")
        lines.append("1. When agent provides information that matches FAQ content, this is CORRECT")
        lines.append("2. When agent provides information that contradicts FAQ content, this is INCORRECT")
        lines.append("3. FAQ data supplements Ready Reckoner - use BOTH for comprehensive validation")
        lines.append("4. Common topics to validate using FAQ:")
        lines.append("   - Location details and connectivity")
        lines.append("   - Amenities list (20+ amenities)")
        lines.append("   - Nearby schools, colleges, hospitals, IT hubs")
        lines.append("   - Project features (gated community, security, infrastructure)")
        lines.append("   - Payment plans, loans, resale policies")
        lines.append("   - Construction support, approvals, plot availability")
        lines.append("5. If agent mentions information from FAQ correctly, award points")
        lines.append("6. If agent provides incomplete or incorrect information covered in FAQ, reduce score")
        lines.append("")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.warning(f"Error extracting FAQ facts: {e}")
        return f"FAQ data available but error in extraction: {e}"


def create_advanced_scoring_prompt(
    transcript: str,
    rubric: Dict[str, Any],
    reckoner_data: Dict[str, Any],
    faq_data: Optional[Dict[str, Any]] = None,
    speaker_segments: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Create advanced prompt for OpenAI with comprehensive evaluation instructions.
    Uses sophisticated prompt engineering techniques for accurate scoring.
    """
    
    # Extract rubric parameters
    categories_text = []
    for category in rubric.get('categories', []):
        cat_name = category.get('name', '')
        cat_desc = category.get('description', '')
        cat_max = category.get('max_points', 0)
        
        categories_text.append(f"\n## {cat_name} (Total: {cat_max} points)")
        categories_text.append(f"   {cat_desc}")
        categories_text.append("")
        
        for sub_param in category.get('sub_parameters', []):
            param_id = sub_param.get('id', '')
            param_name = sub_param.get('name', '')
            param_max = sub_param.get('max_points', 0)
            param_desc = sub_param.get('description', '')
            
            categories_text.append(f"   ### {param_name} (ID: {param_id}) - Max: {param_max} points")
            categories_text.append(f"       {param_desc}")
            categories_text.append("")
            
            # Add scoring guide
            scoring_guide = sub_param.get('scoring_guide', {})
            if scoring_guide:
                categories_text.append("       SCORING GUIDE:")
                for score, guide_text in sorted(scoring_guide.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0, reverse=True):
                    categories_text.append(f"       [{score} points]: {guide_text}")
                categories_text.append("")
            
            # Add evidence requirements
            evidence_req = sub_param.get('evidence_required', [])
            if evidence_req:
                categories_text.append("       EVIDENCE REQUIRED:")
                for ev in evidence_req:
                    categories_text.append(f"       - {ev}")
                categories_text.append("")
            
            # Add validation rules
            validation_rules = sub_param.get('validation_rules', [])
            if validation_rules:
                categories_text.append("       VALIDATION RULES:")
                for rule in validation_rules:
                    categories_text.append(f"       - {rule}")
                categories_text.append("")
    
    rubric_text = "\n".join(categories_text)
    
    # Format reckoner facts
    reckoner_text = extract_reckoner_facts(reckoner_data)
    
    # Format FAQ facts
    faq_text = extract_faq_facts(faq_data) if faq_data else "FAQ data not available."
    
    # Format calling script
    script_text = load_calling_script()
    
    # Format speaker segments
    segments_text = format_speaker_segments(speaker_segments) if speaker_segments else "Not available"
    
    # Create the comprehensive prompt
    prompt = f"""You are an expert call quality auditor for real estate pre-sales calls. Your task is to evaluate a call transcript against a detailed quality rubric with GRANULAR SCORING.

# IMPORTANT: GRANULAR SCORING SYSTEM

Unlike binary yes/no evaluation, this system uses GRANULAR SCORING where each parameter can receive:
- **Any score from 0 to the maximum points** for that parameter
- Scores should reflect the QUALITY and COMPLETENESS of execution
- Use the scoring guides provided for each parameter
- Award partial credit for partial execution
- **NA (Not Applicable) = -1**: When a parameter is genuinely not applicable, mark it as NA by setting score to -1, which automatically awards FULL maximum points

# FATAL PARAMETERS (CRITICAL GATING PARAMETERS)

The following parameters are FATAL - if ANY of them score 0, the entire quality score will be set to 0:
1. **Introduction of brand** (brand_intro): Brand name must be mentioned
2. **No False Commitment / No Wrong Information** (project_knowledge_accuracy): Agent must provide accurate information
3. **Professional Behaviour** (professional): Agent must maintain professional conduct
4. **Avoid being Rude and Unprofessional** (tone_voice_modulation): Agent must not be rude or unprofessional

**IMPORTANT**: These fatal parameters are evaluated normally and contribute to scoring, BUT if any of them scores 0, the final total score will automatically be set to 0 regardless of other parameter scores. Evaluate these parameters strictly and accurately.

Example: If a parameter has max 12 points:
- 12 = Excellent, complete, accurate execution
- 9-12 = Good execution with minor gaps
- 3-6 = Adequate execution with some issues
- 0-3 = Weak execution with major gaps
- 0 = Missing, incorrect, or severely deficient
- -1 = NA (Not Applicable) - automatically receives full 12 points

NOTE: From the example above, score parameters based on their max points and range of scores.

**NA SCORING RULES:**
- Use **score: -1** to indicate NA (Not Applicable)
- NA automatically awards the **FULL maximum points** for that parameter
- Use NA **EXTREMELY SPARINGLY** - only when genuinely not applicable due to call context
- Examples of valid NA scenarios (RARE):
  * Objection Handling: **EXTREMELY RARE** - Only if customer showed ZERO resistance, concerns, objections, hesitation, or pushback of ANY kind throughout entire call. Note: Objections include ANY concerns (property features, pricing, process, information availability, site visits, documentation, redirections to other teams, skepticism, etc.)
  * Follow Up: Customer is completely not interested with absolutely no opportunity for follow-up
  * Thanking Customer: Call ended abruptly or customer was extremely rude making thanks inappropriate
- **CRITICAL FOR OBJECTION HANDLING**: Do NOT mark as NA if customer:
  * Asked questions that weren't answered satisfactorily
  * Expressed any frustration, skepticism, or hesitation
  * Raised concerns about process, information, pricing, features, visits, documentation
  * Was redirected to another team without resolution
  * Showed any form of resistance or pushback
- **Do NOT use NA as a way to avoid evaluation** - only use when truly not applicable
- In rationale, clearly explain WHY the parameter is marked as NA with comprehensive evidence

# CRITICAL EVALUATION PRINCIPLES

## 1. EVIDENCE-BASED SCORING (MANDATORY)
- **Every score MUST be backed by explicit evidence** from the transcript
- **TIMESTAMPS ARE ABSOLUTELY MANDATORY** for EVERY piece of evidence (format: [MM:SS - MM:SS])
- **NO EXCEPTIONS**: Every quote, behavior, or statement MUST have a timestamp
- **Quote verbatim** or paraphrase very closely
- **Never assume or infer** beyond what is explicitly present
- If evidence is weak or absent, score must be lower
- **CRITICAL**: If you cannot find evidence with a verifiable timestamp, you MUST score lower or mark as not present

## 2. WHOLE TRANSCRIPT ANALYSIS (MANDATORY)
- **Analyze the ENTIRE transcript** for each parameter, not isolated sections
- Check if behaviors occur at any point in the conversation
- Do NOT conclude failure based on isolated evidence without checking the full context
- Example: If customer repeats something, check if agent addressed it elsewhere before marking as failure

## 3. NO HALLUCINATION (CRITICAL)
- **Only score what is explicitly present** in the transcript
- **Never invent evidence** or assume behaviors occurred
- If you cannot find clear evidence, state "No evidence found" and score accordingly
- Uncertainty = lower score, not assumed success
- **BRAND NAME RULE (CLOSING / GREETING / ANYWHERE):**
  * Do **NOT** say the agent mentioned the brand name unless the exact brand (e.g., "Adityaram", "Adityaram Property") **actually appears in the transcript text** with a timestamp.
  * Generic closings like "Thank you, sir", "Good day, madam" **WITHOUT the brand text** must **NOT** be treated as brand mention.
  * If the transcript line is in Tamil or mixed Tamil-English (e.g., "தேங்க்யூ... குட் டே மேம்"), you **must still only credit a brand mention when the brand word itself appears** in the transcription.
  * If the transcription is imperfect or partially in Tamil, you **must trust the given text** and **cannot assume** missing English words like the brand name.
  * When scoring parameters that require brand mention (greeting, intro, closing, etc.), **explicitly quote the brand word with timestamp** in both rationale and evidence. If you cannot, treat it as **not mentioned** and score accordingly.

## 4. PROJECT KNOWLEDGE VALIDATION (CRITICAL)
- **Strictly validate ALL factual statements** against BOTH the Ready Reckoner data AND FAQ data provided
- **Use Ready Reckoner for primary validation** of core project facts (pricing, plot sizes, approvals, land extent)
- **Use FAQ data for comprehensive validation** of:
  * Amenities list (20+ amenities)
  * Location details and connectivity information
  * Nearby schools, colleges, hospitals, IT hubs
  * Project features (security, infrastructure, water source, etc.)
  * Payment plans, loans, policies
  * Any other project-related information
- **Critical errors result in 0 score** for project_knowledge_accuracy:
  * Wrong project name
  * Pricing outside Rs. 6000-6300 per sq.ft.
  * Minimum plot size below 617 sq.ft.
  * Wrong approvals
  * Major location errors
- **Extract exact values** mentioned by agent and compare to both Ready Reckoner and FAQ
- Even ONE critical error = 0 score for project_knowledge_accuracy
- **FAQ data supplements Ready Reckoner** - use both sources for comprehensive knowledge validation

## 5. CALLING SCRIPT ADHERENCE
- The calling script shows the IDEAL flow, not mandatory exact wording
- Evaluate if agent achieved the INTENT and STRUCTURE of the script
- Allow natural variations, different ordering, Tamil-English mixing
- Focus on whether key elements were covered, not exact phrases

## 6. CULTURAL AND LINGUISTIC CONTEXT
- **Tamil-English code-mixing is NORMAL** and acceptable
- Do NOT penalize for natural language mixing common in regional calls
- Focus on clarity, professionality, and effectiveness, not language purity
- Only mark down if mixing creates actual communication problems
  * You MUST still understand and interpret Tamil text accurately (including Tamil words written in English letters), but **all findings must come from the actual transcript text with timestamps**, not assumptions.

## 7. TONE AND PROFESSIONALISM
- Default to high scores unless clear negative behavior present
- For tone_voice_modulation: Only score 0 if harsh, rude, abusive, aggressive, disrespectful
- Monotone is not automatically 0 unless it significantly impacts engagement

## 8. OBJECTION HANDLING - BROAD DEFINITION (CRITICAL)
- **Objections include ANY customer resistance, concerns, or pushback** - not just about property/pricing
- **Types of objections to evaluate**:
  * **Property-related**: Price too high, location concerns, size issues, feature adequacy, competitor comparison
  * **Process-related**: Registration process unclear, payment concerns, documentation questions, timeline issues
  * **Information-related**: Questions not answered, being redirected to other teams, incomplete information provided, agent doesn't know details
  * **Service-related**: Frustration with process, skepticism about company, trust issues, dissatisfaction with response
  * **Requirement-related**: Pushback on site visit requirement, timing conflicts, budget misalignment
  * **Implicit objections**: Hesitation, skepticism in tone, repeated questions (indicating dissatisfaction with answers), pushback, resistance
- **Mark as NA ONLY if**: Customer showed ZERO concerns, questions, resistance, or hesitation of ANY kind throughout entire call (extremely rare)
- **Do NOT mark as NA if**: Customer raised any questions that weren't fully answered, expressed frustration, was redirected to another team, showed skepticism, or had any form of resistance

## 9. CONTEXTUAL EVALUATION
- Consider call context: customer interest level, call length, complexity
- Some parameters may genuinely not apply (use NA scoring VERY sparingly, explain thoroughly why)
- Be fair: don't expect perfection, but maintain quality standards
- Customer behavior impacts agent options (e.g., if customer is curt, agent adjusts)
- **CRITICAL FOR OBJECTION HANDLING**: Objections are NOT limited to property features or pricing. They include ANY form of customer resistance, concerns, questions not answered, frustration with process, information gaps, redirections, skepticism, hesitation, or pushback. Analyze the entire call for ALL types of objections.

{segments_text}

# FULL TRANSCRIPT
{transcript}

{reckoner_text}

{faq_text}

# CALLING SCRIPT REFERENCE (IDEAL FLOW)
{script_text}

# QUALITY RUBRIC FOR EVALUATION
{rubric_text}

# YOUR TASK

Evaluate the transcript against EACH parameter in the rubric and assign a score from 0 to max points.

For EACH parameter, provide:

1. **score** (integer): The points awarded (0 to max_points for that parameter, or -1 for NA which awards full points)

2. **max_points** (integer): The maximum possible points for this parameter. These are **weighted** so that the **sum of all max_points across parameters equals the total score (e.g., 100)**. Your per-parameter scores will be **summed directly** to compute the final total. This means:
   - High-weight parameters must have scores that reflect their greater impact.
   - Do **not** treat all parameters equally; always consider the parameter's `max_points` when deciding the score.
   - For the **same quality of performance**, a 5/10 parameter should contribute more to the final total than a 2/3 parameter.

3. **rationale** (string): VERY COMPREHENSIVE and DETAILED explanation (minimum 5-8 sentences) including:
   - **What you looked for**: Clearly state the parameter requirements and expectations
   - **What you found**: Describe ALL relevant behaviors, statements, and actions observed in detail
   - **Complete analysis**: Provide thorough analysis of how the agent performed on this parameter
   - **Score justification**: Explain precisely why this specific score was assigned (reference scoring guide)
   - **Evidence integration**: Reference EVERY piece of evidence with **EXACT TIMESTAMPS** inline (MANDATORY)
   - **Strengths identified**: Highlight what was done well (if applicable) using **bold** for key strengths, **WITH TIMESTAMPS**
   - **Gaps or issues**: Identify ALL weaknesses, omissions, or problems using **bold** for critical issues
   - **Contextual factors**: Consider call flow, customer responses, and situational context
   - **Comparison to ideal**: Compare agent's performance to the calling script expectations
   - **TIMESTAMPS MANDATORY**: Every reference to agent behavior MUST include timestamp [MM:SS - MM:SS]
   - USE **BOLD MARKDOWN** (double asterisks) to emphasize:
     * Key evaluation points
     * Critical strengths or weaknesses
     * **All timestamps** (e.g., **[0:00 - 0:02]**)
     * Crucial facts or statements
     * Score determinants
   - Example: "The agent demonstrated **excellent greeting** at **[0:00 - 0:02]** but **failed to mention brand name** clearly (no evidence found in entire transcript)."

4. **evidence** (array of strings): Include EVERY SINGLE relevant piece of evidence from transcript:
   - **MANDATORY FORMAT**: "[MM:SS - MM:SS] Speaker: Complete verbatim quote or very close paraphrase"
   - **TIMESTAMPS ARE ABSOLUTELY REQUIRED** - NO EXCEPTIONS
   - Include ALL instances where parameter is relevant (do NOT limit to 1-2 examples)
   - If behavior occurs 5 times, include ALL 5 with timestamps
   - Include both positive evidence (what was done well) AND negative evidence (what was missing)
   - **Each evidence piece MUST have exact timestamp** - entries without timestamps are INVALID
   - Quote the ACTUAL words spoken, not summaries
   - **If no evidence with timestamp can be found, the evidence array should be empty [] and score should reflect this**
   - Example: "[0:02 - 0:05] Agent: Good morning sir, this is Uma from Adityaram Property"
   - **WRONG**: "Agent greeted the customer" (no timestamp)
   - **CORRECT**: "[0:00 - 0:02] Agent: Good morning sir"

5. **validation_notes** (string): For project_knowledge_accuracy parameter ONLY:
   - List EVERY factual claim made by agent **WITH EXACT TIMESTAMP** and exact quote
   - **TIMESTAMPS MANDATORY** for each claim: "Claim at [MM:SS - MM:SS]: 'exact quote'"
   - Validate EACH claim against BOTH Ready Reckoner AND FAQ data (Correct ✓ / Incorrect ✗)
   - Show exact values with timestamps: "Agent said 'Rs. 5500 per sq.ft.' **[2:30 - 2:33]** → INCORRECT (Should be Rs. 6000-6300 per Ready Reckoner)"
   - For amenities, location details, schools/hospitals/IT hubs, use FAQ data for validation
   - For pricing, plot sizes, approvals, land extent, use Ready Reckoner for validation
   - Identify ALL discrepancies with detailed explanation and timestamps, indicating which source (Ready Reckoner or FAQ) was used
   - **Format example**: 
     * "✓ Project name 'Adityaram Empire' **[1:15 - 1:17]** - CORRECT (per Ready Reckoner)"
     * "✗ Pricing 'Rs. 5500/sq.ft.' **[2:30 - 2:33]** - INCORRECT (Should be Rs. 6000-6300 per Ready Reckoner)"
     * "✓ Amenities '20+ world class amenities' **[3:10 - 3:12]** - CORRECT (per FAQ)"
     * "✗ Location '5 mins from OMR' **[4:20 - 4:22]** - INCORRECT (Should be 3 mins per FAQ)"
   - For other parameters, this can be empty string ""

# OUTPUT FORMAT

Respond with a single JSON object where each key is a parameter ID and each value is an object with:

```json
{{
  "parameter_id": {{
    "score": <integer 0 to max, or -1 for NA>,
    "max_points": <integer>,
    "rationale": "<comprehensive explanation with timestamps>",
    "evidence": [
      "[MM:SS - MM:SS] Speaker: quote",
      "[MM:SS - MM:SS] Speaker: quote"
    ],
    "validation_notes": "<for project knowledge validation only>"
  }},
  ...
}}
```

**Note on NA scoring:**
- If a parameter is not applicable, set `"score": -1`
- The system will automatically award full max_points for that parameter
- Explain in rationale why it's marked as NA
- Example: `{{"score": -1, "max_points": 12, "rationale": "This parameter is marked as **NA (Not Applicable)** because no objections were raised by the customer throughout the entire call...", "evidence": []}}`

# CRITICAL REMINDERS (MUST FOLLOW)

1. **Score granularly** - use the full range 0 to max, not just extremes
2. **TIMESTAMPS ARE MANDATORY** - EVERY piece of evidence MUST have exact timestamps [MM:SS - MM:SS]
3. **Provide ALL evidence** - include EVERY relevant quote with exact timestamps, not just 1-2 examples
4. **Be VERY detailed** - write 5-8 comprehensive sentences minimum for each rationale
5. **Use bold formatting** - emphasize key points, strengths, weaknesses, critical facts with **bold**
6. **No assumptions** - only score what is explicitly present with verifiable timestamps
7. **Validate facts strictly** - check all project knowledge against Ready Reckoner with exact values and timestamps
8. **Quote verbatim** - use actual words from transcript, not summaries
9. **Consider full context** - analyze the entire transcript, not isolated fragments
10. **Explain thoroughly** - don't just state findings, explain WHY and HOW they impact the score
11. **Reference all evidence** - every evidence piece in the array should be mentioned in rationale with timestamp
12. **NO EVIDENCE WITHOUT TIMESTAMP** - if you cannot find evidence with timestamp, do not claim it exists
13. **NA SCORING** - Use score=-1 EXTREMELY SPARINGLY and only when parameter is genuinely not applicable to the call. NA automatically awards full maximum points. For Objection Handling specifically, objections include ANY concerns, questions, hesitations, frustrations, or resistance throughout the call (not just property/pricing objections). Do NOT mark as NA unless customer showed ZERO concerns of any kind. Clearly explain WHY it's NA with comprehensive evidence.

**EXAMPLES OF GOOD vs BAD RATIONALES:**

❌ BAD (too brief, no bold, missing evidence):
"The agent greeted the customer and introduced themselves. Score: 2/2."

✓ GOOD (detailed, bold emphasis, all evidence with timestamps):
"For the **Greeting & Introduced Self** parameter, the agent demonstrated **excellent performance** by greeting the customer **promptly within the first 2 seconds** with 'Good morning sir' **[0:00 - 0:02]**, which meets the 3-second requirement specified in the rubric. The agent then provided a **clear and professional self-introduction** stating 'This is Uma from Adityaram Property' **[0:02 - 0:05]**, which **properly identifies both the agent's name (Uma) and the company (Adityaram Property)**. The greeting tone was **courteous and professional**, setting a positive tone for the call. The agent also **confirmed the customer's identity** by asking 'Am I speaking to Mr. Ramesh?' **[0:11 - 0:13]**, which demonstrates **proper protocol for reaching the decision maker**. The customer confirmed with 'Yes' **[0:13 - 0:14]**, and the agent acknowledged with 'Thank you for confirmation sir' **[0:15 - 0:17]**. All rubric requirements for this parameter were **fully satisfied**, including timely greeting, clear self-introduction, and professional demeanor. Therefore, the agent earns the **full 2 points** for this parameter."

❌ BAD (vague, no timestamps, no bold):
"The agent mentioned some project details but got the pricing wrong."

✓ GOOD (detailed, specific facts validated, bold for critical issues, ALL with timestamps):
"For **Project Knowledge Accuracy**, the agent provided **mixed results** with some correct information but **critical factual errors** that significantly impact the score. The agent **correctly stated** the project name as 'Adityaram Empire' **[1:15 - 1:17]** and mentioned the location as 'Kelambakkam, OMR' **[1:20 - 1:22]**, which aligns with the Ready Reckoner. The agent also **accurately described** the land extent as '12 acres' **[1:45 - 1:47]** and mentioned '20+ amenities' **[1:50 - 1:52]**, both of which are **correct per the reckoner**. However, the agent made a **CRITICAL ERROR** when stating the pricing as 'Rs. 5500 per square foot' **[2:30 - 2:33]**, which is **INCORRECT** according to the Ready Reckoner that specifies pricing should be between **Rs. 6000-6300 per sq.ft.** This represents a **significant misrepresentation** of nearly **Rs. 500-800 per sq.ft. below the actual price**. The agent also mentioned plot sizes 'starting from 650 square feet' **[2:35 - 2:37]**, which is **acceptable** (Ready Reckoner shows 617 sq.ft. minimum). While the agent demonstrated some project knowledge by correctly identifying several key facts, the **critical pricing error alone warrants a score of 0 points** per the rubric's strict validation rules that explicitly state 'even ONE critical error = 0 score for project_knowledge_accuracy'. The incorrect pricing could **mislead customers**, create **trust issues**, and lead to **serious problems** during the sales process when the actual pricing is disclosed."

**QUALITY CHECK BEFORE SUBMITTING:**
- Is each rationale at least 5-8 detailed sentences with thorough analysis?
- Does each rationale use **bold** formatting extensively for key points?
- **CRITICAL**: Does EVERY behavior/statement mentioned have a timestamp **[MM:SS - MM:SS]**?
- Are ALL relevant evidence pieces included with exact timestamps in evidence array?
- Are quotes actual verbatim text from transcript, not summaries?
- Is the connection between evidence and score explained in detail?
- Does the rationale reference every evidence piece from the evidence array with timestamp?
- **VERIFY**: No evidence piece exists without a timestamp - if no timestamp, remove it or mark as absent

**ONLY return the JSON object, no other text before or after.**
"""
    
    return prompt


def score_transcript_v2(
    transcript: str,
    rubric: Dict[str, Any],
    reckoner_data: Dict[str, Any],
    faq_data: Optional[Dict[str, Any]] = None,
    speaker_segments: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Score transcript using advanced evaluation with granular scoring.
    
    Returns:
        Dictionary with parameter scores, evidence, and validation details
    """
    if not OPENAI_API_KEY:
        raise ValueError("AZURE_KEY or OPENAI_API_KEY environment variable is not set")
    
    # Use Azure OpenAI endpoint if configured
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=AZURE_ENDPOINT
    )
    
    prompt = create_advanced_scoring_prompt(transcript, rubric, reckoner_data, faq_data, speaker_segments)
    
    logger.info(f"Calling OpenAI API with model: {OPENAI_MODEL}")
    logger.info(f"Prompt length: {len(prompt)} characters")
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert call quality auditor specializing in real estate pre-sales calls. "
                        "You evaluate transcripts with GRANULAR SCORING (0 to max points per parameter, or -1 for NA). "
                        "CRITICAL REQUIREMENTS: "
                        "1. **TIMESTAMPS ARE ABSOLUTELY MANDATORY** - EVERY piece of evidence MUST have exact timestamps [MM:SS - MM:SS]. "
                        "2. Write VERY COMPREHENSIVE rationales (5-8+ sentences minimum per parameter). "
                        "3. Include ALL relevant evidence pieces with exact timestamps, not just 1-2 examples. "
                        "4. Use **BOLD MARKDOWN** (double asterisks) to emphasize key points, strengths, weaknesses, timestamps, and critical facts. "
                        "5. Quote VERBATIM from transcript - use actual words spoken, not summaries. "
                        "6. Explain thoroughly - don't just state findings, explain WHY and HOW they impact the score. "
                        "7. Reference every evidence piece in the rationale with timestamps **[MM:SS - MM:SS]**. "
                        "8. Analyze the ENTIRE transcript for context before scoring each parameter. "
                        "9. Strictly validate project knowledge against provided Ready Reckoner data with exact values and timestamps. "
                        "10. NEVER assume or hallucinate - every score is backed by explicit transcript evidence with verifiable timestamps. "
                        "11. **NO EVIDENCE WITHOUT TIMESTAMP** - if you cannot find evidence with timestamp, do not claim it exists. "
                        "12. **NA SCORING**: Use score=-1 EXTREMELY SPARINGLY when a parameter is genuinely not applicable. NA awards FULL points automatically. For Objection Handling, objections include ANY concerns/resistance (property, pricing, process, information gaps, redirections, frustration, skepticism, etc.) - mark as NA only if ZERO concerns of any kind throughout entire call. "
                        "You respond ONLY with a single valid JSON object, no other text."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent, accurate scoring
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        logger.info(f"OpenAI response received, length: {len(result_text)}")
        
        # Parse JSON response
        scoring_results = json.loads(result_text)
        
        return scoring_results
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI JSON response: {e}")
        logger.error(f"Response was: {result_text[:500]}...")
        raise ValueError(f"Invalid JSON response from OpenAI: {e}")
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise


def check_fatal_parameters(
    scoring_results: Dict[str, Any],
    rubric: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Check fatal parameters. If any fatal parameter scores 0, the entire score should be 0.
    
    Fatal parameters (score 0 = fatal):
    1. Introduction of brand (brand_intro)
    2. No False Commitment (checked via project_knowledge_accuracy - wrong info indicates false commitment)
    3. No Wrong Information (project_knowledge_accuracy)
    4. Professional Behaviour (professional)
    5. Avoid being Rude and Unprofessional (tone_voice_modulation)
    
    Returns:
        Tuple of (is_fatal_failed, list of failed_fatal_params)
    """
    fatal_param_mapping = {
        "brand_intro": "No introduction of brand",
        "project_knowledge_accuracy": "Wrong Information / False Commitment",
        "professional": "No Professional Behaviour",
        "tone_voice_modulation": "Avoid being Rude and Unprofessional"
    }
    
    failed_fatal_params = []
    
    for param_id, param_description in fatal_param_mapping.items():
        result = scoring_results.get(param_id, {})
        param_score = result.get('score', 0)
        
        # Handle NA scoring (NA = -1 awards full points, so not fatal)
        if param_score == -1:
            continue
        
        # Check if score is 0 (fatal)
        if param_score == 0:
            failed_fatal_params.append(f"{param_description} ({param_id})")
            logger.warning(f"FATAL PARAMETER FAILED: {param_description} ({param_id}) scored 0")
    
    is_fatal = len(failed_fatal_params) > 0
    
    if is_fatal:
        logger.error(f"FATAL PARAMETERS FAILED - Score will be set to 0. Failed parameters: {', '.join(failed_fatal_params)}")
    else:
        logger.info("All fatal parameters passed - normal scoring will proceed")
    
    return is_fatal, failed_fatal_params


def compile_final_report(
    scoring_results: Dict[str, Any],
    rubric: Dict[str, Any],
    transcript_length: int,
    num_segments: int
) -> Dict[str, Any]:
    """
    Compile final scoring report with summary and detailed breakdowns.
    Checks fatal parameters first - if any fatal parameter scores 0, total score is set to 0.
    """
    # Define fatal parameters that gate the score but don't contribute to it
    fatal_param_ids = {
        "brand_intro",
        "project_knowledge_accuracy", 
        "professional",
        "tone_voice_modulation"
    }
    
    # Check fatal parameters first
    is_fatal_failed, failed_fatal_params = check_fatal_parameters(scoring_results, rubric)
    
    # Total possible is always the rubric total (100)
    # Fatal parameters are evaluated but don't contribute to the score calculation
    # However, total_possible remains 100 for display purposes
    total_possible = rubric.get('total_points', 100)
    
    total_awarded = 0
    
    # Organize results by category
    category_scores = {}
    detailed_scores = []
    
    for category in rubric.get('categories', []):
        cat_id = category.get('id')
        cat_name = category.get('name')
        # Category max from rubric (includes all parameters)
        cat_max = category.get('max_points', 0)
        # Category awarded excludes fatal parameters from calculation
        cat_awarded = 0
        cat_details = []
        
        for sub_param in category.get('sub_parameters', []):
            param_id = sub_param.get('id')
            param_name = sub_param.get('name')
            param_max = sub_param.get('max_points', 0)
            is_fatal = param_id in fatal_param_ids
            
            # Get scoring result
            result = scoring_results.get(param_id, {})
            param_score = result.get('score', 0)
            rationale = result.get('rationale', 'No rationale provided')
            evidence = result.get('evidence', [])
            validation_notes = result.get('validation_notes', '')
            is_na = False
            
            # Handle NA scoring: -1 means Not Applicable and awards full points
            if param_score == -1:
                logger.info(f"Parameter {param_id} marked as NA, awarding full {param_max} points")
                param_score = param_max
                is_na = True
            # Ensure score is within bounds
            elif param_score < 0:
                logger.warning(f"Score for {param_id} was negative ({param_score}), setting to 0")
                param_score = 0
            elif param_score > param_max:
                logger.warning(f"Score for {param_id} was above max ({param_score} > {param_max}), setting to {param_max}")
                param_score = param_max
            
            # Only add to category and total if NOT a fatal parameter
            # Fatal parameters are evaluated but don't contribute to score calculation
            if not is_fatal:
                cat_awarded += param_score
                total_awarded += param_score
            
            param_detail = {
                "id": param_id,
                "name": param_name,
                "max_points": param_max,
                "points_awarded": param_score,  # UI compatibility
                "score": param_score,
                "percentage": round((param_score / param_max * 100), 2) if param_max > 0 else 0,
                "rationale": rationale,
                "evidence": evidence,
                "validation_notes": validation_notes,
                "response": "V2",  # Indicator for V2 scoring
                "is_na": is_na,  # Indicator for NA (Not Applicable) scoring
                "is_fatal": is_fatal  # Indicator that this is a fatal parameter (gates score but doesn't contribute)
            }
            
            cat_details.append(param_detail)
            detailed_scores.append(param_detail)
        
        category_scores[cat_id] = {
            "name": cat_name,
            "max_points": cat_max,
            "score": cat_awarded,
            "percentage": round((cat_awarded / cat_max * 100), 2) if cat_max > 0 else 0,
            "parameters": cat_details
        }
    
    # If any fatal parameter failed, set total score to 0
    if is_fatal_failed:
        logger.warning(f"FATAL PARAMETER CHECK: Setting total score to 0 due to failed fatal parameters: {', '.join(failed_fatal_params)}")
        total_awarded = 0
        # Note: We still keep all the parameter scores in detailed_scores for reference
        # Only the total_score and percentage are set to 0
    
    percentage = round((total_awarded / total_possible * 100), 2) if total_possible > 0 else 0
    
    if is_fatal_failed:
        logger.info(f"Scoring complete (FATAL FAILED): {total_awarded}/{total_possible} ({percentage}%) - Failed fatal params: {', '.join(failed_fatal_params)}")
    else:
        logger.info(f"Scoring complete: {total_awarded}/{total_possible} ({percentage}%)")
    
    # Return format compatible with existing UI
    metadata = {
        "model_used": OPENAI_MODEL,
        "transcript_length": transcript_length,
        "num_segments": num_segments,
        "scoring_system": "granular_v2",
        "version": "2.0"
    }
    
    # Add fatal parameter information to metadata
    if is_fatal_failed:
        metadata["fatal_parameter_failed"] = True
        metadata["failed_fatal_parameters"] = failed_fatal_params
        # Create a user-friendly fatal error reason message
        fatal_reason = f"Score set to 0 due to FATAL parameter failure(s): {', '.join(failed_fatal_params)}"
        metadata["fatal_error_reason"] = fatal_reason
    else:
        metadata["fatal_parameter_failed"] = False
        metadata["fatal_error_reason"] = None
    
    # Build return object with fatal error information at top level for easy access
    result = {
        "rubric_title": rubric.get('title', 'Empire Pre-Sales Call Quality Audit'),
        "total_points": total_possible,
        "total_score": total_awarded,
        "percentage": percentage,
        "criteria_scores": detailed_scores,  # UI expects this - includes all parameter scores for reference
        "metadata": metadata
    }
    
    # Add fatal error reason at top level for easy UI access
    if is_fatal_failed:
        result["fatal_error_reason"] = metadata["fatal_error_reason"]
        result["failed_fatal_parameters"] = failed_fatal_params
    
    return result


def score_transcript_main(transcript_data: Dict[str, Any], rubric_path: str = None) -> Dict[str, Any]:
    """
    Main entry point for transcript scoring with version 2 system.
    
    Args:
        transcript_data: Dictionary containing:
            - transcription: Full transcript text
            - speaker_segments: List of speaker segments with timing (optional)
        rubric_path: Path to rubric YAML file (defaults to empire_rubric_v2.yaml)
    
    Returns:
        Comprehensive scoring report
    """
    logger.info("Starting transcript scoring with V2 system (granular scoring)")
    
    transcript = transcript_data.get("transcription", "")
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty or missing")
    
    logger.info(f"Transcript length: {len(transcript)} characters")
    
    # Load rubric
    rubric = load_rubric_v2(rubric_path)
    logger.info(f"Loaded rubric v2: {rubric.get('title', 'Unknown')}")
    
    # Load Ready Reckoner (both Empire and HappiNest)
    reckoner_data = load_project_reckoner()
    logger.info(f"Loaded Ready Reckoner data for both projects")
    
    # Load FAQ data (both Empire and HappiNest)
    faq_data = load_faq_data()
    logger.info(f"Loaded FAQ data for both projects")
    
    # Get speaker segments
    speaker_segments = transcript_data.get("speaker_segments", [])
    logger.info(f"Speaker segments: {len(speaker_segments)}")
    
    # Perform scoring
    scoring_results = score_transcript_v2(
        transcript=transcript,
        rubric=rubric,
        reckoner_data=reckoner_data,
        faq_data=faq_data,
        speaker_segments=speaker_segments
    )
    
    # Compile final report
    final_report = compile_final_report(
        scoring_results=scoring_results,
        rubric=rubric,
        transcript_length=len(transcript),
        num_segments=len(speaker_segments)
    )
    
    return final_report

