"""
Transcript scoring service using OpenAI for yes/no/na classification.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import yaml

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL, AZURE_ENDPOINT

logger = logging.getLogger(__name__)


def load_rubric(rubric_path: str = None) -> Dict[str, Any]:
    """Load the rubric YAML file."""
    if rubric_path is None:
        # Default to empire_rubric.yaml in the same directory as this file
        rubric_file = Path(__file__).parent / "empire_rubric.yaml"
    else:
        rubric_file = Path(rubric_path)
        if not rubric_file.exists() and not rubric_file.is_absolute():
            # Try relative to this file's directory
            rubric_file = Path(__file__).parent / rubric_path
            if not rubric_file.exists():
                # Try relative to project root
                rubric_file = Path(__file__).parent.parent / rubric_path
    
    if not rubric_file.exists():
        raise FileNotFoundError(f"Rubric file not found: {rubric_path or 'empire_rubric.yaml'}")
    
    logger.info(f"Loading rubric from: {rubric_file}")
    try:
        with open(rubric_file, 'r', encoding='utf-8') as f:
            rubric = yaml.safe_load(f)
        if rubric is None:
            raise ValueError("Rubric file is empty or contains no valid YAML")
        return rubric
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {rubric_file}: {e}")
        raise ValueError(f"Failed to parse rubric YAML file: {e}") from e
    except Exception as e:
        logger.error(f"Error loading rubric file {rubric_file}: {e}")
        raise


def load_project_knowledge() -> Dict[str, Any]:
    """Load project knowledge from combined JSON file for both Empire and HappiNest."""
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
                
                logger.info(f"Loaded combined project knowledge for both Empire and HappiNest")
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
        logger.info(f"Loading Empire project knowledge from: {empire_file}")
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
        logger.warning(f"Empire project knowledge file not found: {empire_file}")
    
    # Load HappiNest data
    happinest_file = base_path / "HappiNest" / "happinest_extracted_data.json"
    if not happinest_file.exists():
        # Also check Empire folder as fallback
        happinest_file = base_path / "Empire" / "happinest_extracted_data.json"
    
    if happinest_file.exists():
        logger.info(f"Loading HappiNest project knowledge from: {happinest_file}")
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
        logger.warning(f"HappiNest project knowledge file not found")
    
    logger.info(f"Loaded project knowledge for both Empire and HappiNest")
    return combined_data


def _format_time(seconds: float) -> str:
    """Format seconds as M:SS for readability."""
    try:
        s = float(seconds)
    except (TypeError, ValueError):
        return "0:00"
    if s < 0:
        s = 0
    minutes = int(s // 60)
    secs = int(s % 60)
    return f"{minutes}:{secs:02d}"


def _extract_project_facts_for_validation(project_knowledge: Dict[str, Any]) -> str:
    """Extract and format key project facts from JSON for validation against agent statements.
    Handles both Empire and HappiNest project knowledge."""
    if not project_knowledge or "files" not in project_knowledge:
        return "Project knowledge data not available."
    
    try:
        facts = []
        files = project_knowledge.get("files", {})
        
        # Extract Empire facts
        empire_reckoner = files.get("empire_reckoner_excel", {})
        if empire_reckoner.get("status") == "success":
            empire_sheets = empire_reckoner.get("sheets", {})
            # Try different possible sheet names for Empire
            empire_sheet_data = None
            for sheet_name in ["Sheet2", "Ready Reckoner", "Ready Reckoner - FY 2025 - 26(A"]:
                if sheet_name in empire_sheets:
                    sheet_info = empire_sheets[sheet_name]
                    if isinstance(sheet_info, dict) and "data" in sheet_info:
                        empire_sheet_data = sheet_info["data"]
                    elif isinstance(sheet_info, list):
                        empire_sheet_data = sheet_info
                    if empire_sheet_data:
                        break
            
            if empire_sheet_data and len(empire_sheet_data) > 0:
                # Get the first row which contains the main project information
                main_data = empire_sheet_data[0] if isinstance(empire_sheet_data[0], dict) else {}
                
                facts.append("=" * 80)
                facts.append("**CRITICAL PROJECT FACTS FOR VALIDATION - ADITYARAM EMPIRE PHASE 2:**")
                facts.append("=" * 80)
                facts.append("")
                facts.append("Use these EXACT values to validate agent statements about Empire project. Any deviation = 'no' for project_knowledge.")
                facts.append("")
        
                # Extract Empire project facts
                project_name = main_data.get("Project", "").strip()
                if project_name:
                    facts.append(f"**Project Name:** {project_name}")
                    facts.append("  → **CORRECT:** 'Adityaram Empire' or 'Adityaram Empire Phase 2' or 'Empire Phase 2'")
                    facts.append("  → **WRONG:** Any other project name")
                    facts.append("")
                
                location = main_data.get("Location", "").strip()
                if location:
                    facts.append(f"**Location:** {location}")
                    facts.append("")
                
                approval = main_data.get("Approval", "").strip()
                if approval:
                    facts.append(f"**Approval:** {approval}")
                    facts.append("")
                
                rate_text = main_data.get("Rate per sqft", "").strip()
                if rate_text:
                    facts.append(f"**Rate per sqft (CRITICAL - MUST VALIDATE):**")
                    facts.append(f"  Source data: {rate_text}")
                    facts.append("  → **CORRECT VALUES:** Rs. 6000/- per sq.ft. (Early Bird Offer) OR Rs. 6300/- per sq.ft. (Actual Price)")
                    facts.append("  → **VALIDATION RULE:** Agent MUST mention price between Rs. 6000-6300 per sq.ft.")
                    facts.append("  → **AUTOMATIC 'no':** Any price outside this range (e.g., Rs. 5500, Rs. 5000, Rs. 7000, etc.) = 'no'")
                    facts.append("")
                
                plot_size = main_data.get("Actual Plot Size", "").strip()
                if plot_size:
                    facts.append(f"**Plot Sizes (CRITICAL - MUST VALIDATE):**")
                    facts.append(f"  Source data: {plot_size}")
                    facts.append("  → **CORRECT MINIMUM:** 617 sq.ft. (or 650 sq.ft. as acceptable variation)")
                    facts.append("  → **CORRECT MAXIMUM:** 3777 sq.ft.")
                    facts.append("  → **VALIDATION RULE:** Agent MUST mention minimum plot size as 617 sq.ft. or higher (650 sq.ft. acceptable)")
                    facts.append("  → **AUTOMATIC 'no':** Any mention of minimum plot size below 617 sq.ft. (e.g., 500 sq.ft., 400 sq.ft.) = 'no'")
                    facts.append("")
                
                for key in ["Price Onwards", "Land Extent", "Total Units", "Status"]:
                    value = main_data.get(key, "").strip()
                    if value:
                        facts.append(f"**{key}:** {value}")
                        facts.append("")
        
        # Extract HappiNest facts
        happinest_reckoner = files.get("happinest_reckoner_excel", {})
        if happinest_reckoner.get("status") == "success":
            happinest_sheets = happinest_reckoner.get("sheets", {})
            happinest_sheet_data = None
            for sheet_name in happinest_sheets.keys():
                sheet_info = happinest_sheets[sheet_name]
                if isinstance(sheet_info, dict) and "data" in sheet_info:
                    happinest_data_list = sheet_info["data"]
                    if happinest_data_list and len(happinest_data_list) > 0:
                        happinest_sheet_data = happinest_data_list
                        break
            
            if happinest_sheet_data and len(happinest_sheet_data) > 0:
                # Get the first row which contains the main project information
                happinest_main_data = happinest_sheet_data[0] if isinstance(happinest_sheet_data[0], dict) else {}
                
                facts.append("")
                facts.append("=" * 80)
                facts.append("**CRITICAL PROJECT FACTS FOR VALIDATION - HAPPINEST:**")
                facts.append("=" * 80)
                facts.append("")
                facts.append("Use these EXACT values to validate agent statements about HappiNest project. Any deviation = 'no' for project_knowledge.")
                facts.append("")
                
                # Extract HappiNest project facts
                happinest_project = happinest_main_data.get("Project", "").strip()
                if happinest_project:
                    facts.append(f"**Project Name:** {happinest_project}")
                    facts.append("  → **CORRECT:** 'HappiNest' or 'Happinest' or variations")
                    facts.append("")
                
                happinest_location = happinest_main_data.get("Location", "").strip()
                if happinest_location:
                    facts.append(f"**Location:** {happinest_location}")
                    facts.append("")
                
                happinest_approval = happinest_main_data.get("Approval", "").strip()
                if happinest_approval:
                    facts.append(f"**Approval:** {happinest_approval}")
                    facts.append("")
                
                happinest_rate = happinest_main_data.get("Rate per sqft", "").strip()
                if happinest_rate:
                    facts.append(f"**Rate per sqft (CRITICAL - MUST VALIDATE):**")
                    facts.append(f"  Source data: {happinest_rate}")
                    facts.append("  → **VALIDATION RULE:** Agent MUST mention the correct price from source data")
                    facts.append("")
                
                happinest_plot_size = happinest_main_data.get("Plot Size", "").strip()
                if happinest_plot_size:
                    facts.append(f"**Plot Sizes (CRITICAL - MUST VALIDATE):**")
                    facts.append(f"  Source data: {happinest_plot_size}")
                    facts.append("  → **VALIDATION RULE:** Agent MUST mention correct plot sizes from source data")
                    facts.append("")
                
                for key in ["Price\nonwards", "Price onwards", "Land Extent", "Total Units", "Status"]:
                    value = happinest_main_data.get(key, "").strip()
                    if value:
                        value = main_data.get(key, "").strip()
                    if value:
                        facts.append(f"**{key}:** {value}")
                        facts.append("")
        
        # Extract HappiNest facts
        happinest_reckoner = files.get("happinest_reckoner_excel", {})
        if happinest_reckoner.get("status") == "success":
            happinest_sheets = happinest_reckoner.get("sheets", {})
            happinest_sheet_data = None
            for sheet_name in happinest_sheets.keys():
                sheet_info = happinest_sheets[sheet_name]
                if isinstance(sheet_info, dict) and "data" in sheet_info:
                    happinest_data_list = sheet_info["data"]
                    if happinest_data_list and len(happinest_data_list) > 0:
                        happinest_sheet_data = happinest_data_list
                        break
            
            if happinest_sheet_data and len(happinest_sheet_data) > 0:
                # Get the first row which contains the main project information
                happinest_main_data = happinest_sheet_data[0] if isinstance(happinest_sheet_data[0], dict) else {}
                
                facts.append("")
                facts.append("=" * 80)
                facts.append("**CRITICAL PROJECT FACTS FOR VALIDATION - HAPPINEST:**")
                facts.append("=" * 80)
                facts.append("")
                facts.append("Use these EXACT values to validate agent statements about HappiNest project. Any deviation = 'no' for project_knowledge.")
                facts.append("")
                
                # Extract HappiNest project facts
                happinest_project = happinest_main_data.get("Project", "").strip()
                if happinest_project:
                    facts.append(f"**Project Name:** {happinest_project}")
                    facts.append("  → **CORRECT:** 'HappiNest' or 'Happinest' or variations")
                    facts.append("")
                
                happinest_location = happinest_main_data.get("Location", "").strip()
                if happinest_location:
                    facts.append(f"**Location:** {happinest_location}")
                    facts.append("")
                
                happinest_approval = happinest_main_data.get("Approval", "").strip()
                if happinest_approval:
                    facts.append(f"**Approval:** {happinest_approval}")
                    facts.append("")
                
                happinest_rate = happinest_main_data.get("Rate per sqft", "").strip()
                if happinest_rate:
                    facts.append(f"**Rate per sqft (CRITICAL - MUST VALIDATE):**")
                    facts.append(f"  Source data: {happinest_rate}")
                    facts.append("  → **VALIDATION RULE:** Agent MUST mention the correct price from source data")
                    facts.append("")
                
                happinest_plot_size = happinest_main_data.get("Plot Size", "").strip()
                if happinest_plot_size:
                    facts.append(f"**Plot Sizes (CRITICAL - MUST VALIDATE):**")
                    facts.append(f"  Source data: {happinest_plot_size}")
                    facts.append("  → **VALIDATION RULE:** Agent MUST mention correct plot sizes from source data")
                    facts.append("")
                
                for key in ["Price\nonwards", "Price onwards", "Land Extent", "Total Units", "Status"]:
                    value = happinest_main_data.get(key, "").strip()
                    if value:
                        facts.append(f"**{key}:** {value}")
                        facts.append("")
        
        facts.append("")
        facts.append("=" * 80)
        facts.append("**VALIDATION PROCESS (FOLLOW THESE STEPS):**")
        facts.append("=" * 80)
        facts.append("1. First, identify which project the agent is discussing (Empire or HappiNest)")
        facts.append("2. Extract the EXACT pricing value mentioned by the agent")
        facts.append("3. Extract the EXACT plot size range mentioned by the agent")
        facts.append("4. Compare agent's statements against the CORRECT VALUES for the specific project mentioned")
        facts.append("5. If agent mentions wrong project name → 'no'")
        facts.append("6. If agent mentions pricing/plot sizes that don't match the project facts → 'no'")
        facts.append("7. **Even ONE critical error = automatic 'no' for project_knowledge**")
        facts.append("8. Do NOT mark 'yes' if pricing or plot sizes are incorrect, even if other details are correct")
        facts.append("")
        facts.append("**FULL RECKONER DATA (for additional reference):**")
        facts.append(json.dumps(project_knowledge, indent=2))
        
        return "\n".join(facts)
    except Exception as e:
        logger.warning(f"Error extracting project facts: {e}")
        return json.dumps(project_knowledge, indent=2) if project_knowledge else "Project knowledge data not available."


def create_scoring_prompt(
    transcript: str,
    rubric: Dict[str, Any],
    project_knowledge: Dict[str, Any],
    speaker_segments: List[Dict[str, Any]] | None = None,
) -> str:
    """Create the prompt for OpenAI to score the transcript, with contextual reasoning and timing."""
    
    # Format criteria descriptions
    criteria_text = ""
    for idx, criterion in enumerate(rubric['criteria'], 1):
        criteria_text += f"\n{idx}. {criterion['name']} (ID: {criterion['id']})\n"
        criteria_text += f"   Description: {criterion['description']}\n"
        criteria_text += f"   Max Points: {criterion['max_points']}\n"
    
    # Format project knowledge with extracted key facts for validation
    knowledge_text = _extract_project_facts_for_validation(project_knowledge) if project_knowledge else "Not available"

    # Format speaker segments with timing (helps for confidence, buffering, call control, etc.)
    segments_text = "Not available"
    if speaker_segments:
        lines: List[str] = []
        sorted_segments = sorted(
            speaker_segments,
            key=lambda seg: seg.get("start_time", 0.0)
        )
        last_end = None
        for seg in sorted_segments:
            speaker = seg.get("speaker", "Unknown")
            start = seg.get("start_time", 0.0)
            end = seg.get("end_time", start)
            text = str(seg.get("text", "")).strip()
            start_str = _format_time(start)
            end_str = _format_time(end)
            if last_end is not None:
                gap = max(0.0, float(start) - float(last_end))
                if gap >= 2.5:
                    lines.append(f"- SILENCE ~{gap:.1f}s between { _format_time(last_end) } and { start_str}")
            lines.append(f"- {speaker} [{start_str} - {end_str}]: {text}")
            last_end = end
        segments_text = "\n".join(lines[:200])  # cap to avoid overly long prompts
    
    prompt = f"""You are an expert call quality auditor evaluating a pre-sales real estate call transcript for a real estate project (Adityaram Empire).

**CALL FLOW & SCRIPT EXPECTATIONS (USE AS GUIDELINES, NOT EXACT WORDING):**
- The original Adityaram Empire calling script describes an IDEAL flow, validate them by understandint the context of the script and the call transcript.
- Treat the script as a reference for **intent and structure**, NOT for exact phrases.
- The agent can use different wording, different ordering, and a mix of English/Tamil, as long as the **meaning of each rubric criterion is satisfied**.
- A criterion should be marked **\"yes\"** whenever the agent's behaviour meets the intent of that criterion, even if they do not follow the exact sample sentences from the script.
- Only mark **\"no\"** when, based on the actual conversation, the behaviour for that parameter is missing, wrong, or below expectation.

**PROJECT KNOWLEDGE VALIDATION (CRITICAL FOR 'project_knowledge' PARAMETER ONLY):**
The data below contains the official Ready Reckoner facts for Adityaram Empire Phase 2, extracted from empire_extracted_data.json.
- You MUST use this data **ONLY when scoring the 'project_knowledge' criterion (ID: project_knowledge)**.
- For all other parameters, do NOT validate project facts; focus only on behavioral criteria.

**VALIDATION PROCESS:**
1. Extract the exact values mentioned by the agent (pricing, plot sizes, project name, etc.)
2. Compare them against the CORRECT VALUES listed in the project facts below
3. Follow the validation rules specified for each fact
4. Any deviation from the correct values = automatic 'no' for project_knowledge

**PROJECT FACTS FOR VALIDATION:**
{knowledge_text}

**SPEAKER SEGMENTS WITH TIMING (CRITICAL - USE EXACT TIMESTAMPS FROM HERE):**
{segments_text}

**TRANSCRIPT TO EVALUATE:**
{transcript}

**TIMESTAMP USAGE:**
- If speaker segments with timing are provided above, you MUST use those EXACT timestamps [MM:SS - MM:SS] in your evidence snippets and rationale.
- When citing evidence, always include the exact timestamp where it appears.
- If multiple instances of relevant behavior occur, cite ALL of them with their timestamps.
- Also nalyze the timing gaps and segment durations shown in the speaker segments to understand the flow of the call and use them also to score the parameters accordingly.

**SCORING RUBRIC CRITERIA:**
{criteria_text}

**INSTRUCTIONS:**
For each criterion, evaluate the transcript based on the **real call context** (customer interest level, call length, language used, objections raised, etc.) and decide one of: "yes", "no", or "na"
- "yes": The criterion was met/followed appropriately.
- "no": The criterion was not met/was not followed.
- "na": The criterion is not applicable to this call context, meaning it genuinely did not need to be evaluated in this call. Maybe customer was not interested or wanted to skip that part of the call.

**CRITICAL: WHOLE TRANSCRIPT CONTEXT ANALYSIS (MANDATORY FOR ALL PARAMETERS):**
- **ALWAYS analyze the ENTIRE transcript from start to finish** when scoring each parameter. Do NOT evaluate based on isolated evidence snippets alone.
- **Understand the full conversation flow**: A customer repeating a request does NOT automatically mean the agent failed to listen. The agent may have:
  - Acknowledged the request earlier but the customer didn't hear/understand
  - Provided partial information that the customer wanted more of
  - Addressed it in a different way that the customer didn't recognize
  - Been in the process of providing it when the customer interrupted
- You must **NOT assume** that the customer repeated information (for example, their budget, location, or requirements) unless you can quote **at least one distinct utterances with different timestamps** where the same information is clearly stated. If you cannot find such utterances in the transcript, you must **not** use "customer had to repeat themselves" as a reason for marking "no" on any criterion.
NOTE: DO NOT ASSUME ANYTHING, USE THE GIVEN DOCS AND TRANSCRIPT TO SCORE THE PARAMETERS WITH PROOF.

**IMPORTANT:**
- DO NOT require the agent to repeat the **exact script wording** except the brand name ( Adithya Ram Properties or Adithya Ram in any form). Focus on whether they achieved the **intent** of each criterion.
- For "na" responses, consider if the criterion could not be evaluated or was genuinely **not required** due to call context, and clearly explain WHY it is "na".
- Do **NOT** use "na" just because the agent gave vague, weak or incomplete information; in those cases the expected behaviour was required but not done properly, so the answer should be "no" with an explanation.
- Treat "yes" as requiring **moderate to high confidence** (approximately 75–80% or higher). If you are uncertain or the evidence is weak/ambiguous, prefer "no" or "na" and explain why.
- Be strict with requirements **inside the rubric descriptions themselves** – if a rubric description explicitly says "ALL must be present", then missing ANY of those specifically required elements should still lead to "no".
- For project knowledge, **STRICTLY verify** every factual statement against the extracted project facts provided above. **CRITICAL ERRORS** that automatically result in "no": (1) Wrong project name (not "Adityaram Empire" or variations), (2) **PRICING ERRORS: Any price mentioned outside Rs. 6000-6300 per sq.ft. range (e.g., Rs. 5500, Rs. 5000, Rs. 7000) = automatic 'no'**, (3) **PLOT SIZE ERRORS: Any mention of minimum plot size below 617 sq.ft. (e.g., 500 sq.ft., 400 sq.ft.) = automatic 'no'**, (4) Wrong approvals, (5) Mentioning amenities/features not in reckoner. **Even ONE critical error = automatic 'no'**. You MUST extract the exact values the agent mentioned and compare them against the CORRECT VALUES in the project facts section above. Do NOT mark "yes" if pricing or plot sizes are incorrect, even if other details are correct.
- When evaluating **closing_script (ID: closing_script)**, the agent **MUST** mention the **brand name in the closing part of the call itself** (near the end, around the final thanks/farewell) for the answer to be "yes". Treat any clear closing line that mentions the brand name (for example, "Thank you for connecting Adithya Ram Property. Have a great day") as strong evidence **FOR** this criterion. Accept spelling/spacing variations of the brand such as "Adityaram Property", "Adithiram Property", "Adityaram Properties", "Adithiram Properties", "Adithya Ram Property", "Adithya Ram" etc. If the closing only says something like "Thank you" or "Thanks" or "Thank you, bye" **without the brand name**, you **MUST** score **"no"** for closing_script even if the overall closing tone is polite. If the brand name appears only earlier in the call but is missing in the final closing lines, you **MUST** still score **"no"** for closing_script.
- Reuse relevant utterances across criteria: e.g., a single line like "Thank you for connecting Adithya Ram Property. Have a great day" should contribute evidence for BOTH **thanking_customer** and **closing_script**, with the same timestamps.
- For **tone_voice (ID: tone_voice)**, default to **"yes"** unless there is clear evidence of harsh, rude, abusive or aggressive words, a raised/angry tone, or disrespect toward the customer (for example, shouting, arguing, mocking, or clearly irritated delivery). Only when such negative behaviour is present should you mark "no" for tone_voice.
- ALWAYS base your answers on explicit evidence from the transcript and/or timing data. If you cannot find clear supporting evidence for a \"yes\" (for example, you cannot quote or closely paraphrase any relevant line), default to \"na\" as appropriate and explain why.
- For every criterion, you MUST provide **comprehensive reasoning** that includes ALL relevant points (not just 2-4 sentences, but all reasons that support your decision).
- When writing the "rationale" and "evidence_snippet" fields, you may emphasise the MOST IMPORTANT words or short phrases by wrapping them in Markdown-style bold markers, e.g. **critical error**, **brand name missing in closing**, **excellent probing on budget**. Do not overuse bold; reserve it only for the key ideas.
- **CRITICAL: Include exact timestamps** for every piece of evidence you cite. Use the format [MM:SS - MM:SS] or [MM:SS] for single timestamps. If speaker segments with timing are provided, use those exact timestamps. If only transcript text is available, estimate timestamps based on call flow and segment positions.
- For every criterion, **quote or paraphrase ALL relevant phrases** from the transcript and indicate **exact timestamps** where they occur. Include multiple evidence points if relevant (e.g., if something appears multiple times, cite all occurrences with timestamps).

**SPECIAL RULES FOR LANGUAGE & CLARITY:**
- Tamil–English code-mixing is **allowed and normal** for these calls. Do **NOT** mark "no" for **language_grammar** or **clarity_speech** just because the associate frequently mixes Tamil and English.
- For **language_grammar (ID: language_grammar)**, focus on whether the sentences are generally grammatically acceptable in the mixed Tamil/English the customer uses, and whether the word choice is professional and respectful.
- For **clarity_speech (ID: clarity_speech)**, focus on whether the customer clearly understands and responds relevantly; only mark "no" if speed, mumbling, very broken language, or other issues clearly make it hard to understand, even if mixing is present.

**EVIDENCE-REASONING ALIGNMENT (MANDATORY):**
- **Evidence MUST directly support your rationale**: Every piece of evidence cited in "evidence_snippet" must be explicitly explained in the "rationale" field. The rationale must clearly explain HOW each piece of evidence supports your decision (yes/no/na).
- **Only cite relevant evidence**: **Strictly** include all evidence that is relevant to the specific parameter being scored. Do NOT include evidence that is unrelated to the criterion.
- **Explain the connection**: In your rationale, explicitly state how each cited evidence snippet demonstrates the presence or absence of the required behavior. For example:
  - If scoring "yes": "The agent demonstrated [parameter] by [specific action] as shown in [evidence quote] [timestamp], which indicates [explanation]."
  - If scoring "no": "The agent failed to demonstrate [parameter] because [specific issue], evidenced by [evidence quote] [timestamp], which shows [explanation]."
- **Avoid contradictory evidence**: Do NOT cite evidence that contradicts your answer. If you mark "yes" for a parameter, do not include evidence that suggests the behavior was missing. If you mark "no", do not include evidence that suggests the behavior was present (unless you are explaining why that evidence is insufficient or outweighed by other factors).
- **Evidence must match the parameter**: Ensure that the evidence you cite actually relates to the specific criterion being evaluated. For example, evidence about greeting should only be cited for greeting-related parameters, not for other parameters.

NOTE: Instead of providing a single evidence snippet, provide all the evidence snippets that are relevant to the criterion. Also always find the evidence snippets from the transcript and provide them in the evidence_snippet field.

**OUTPUT FORMAT (STRICT):**
Respond with a single JSON object.
- Each key must be a criterion ID.
- Each value must be an object with:
  - "answer": "yes" | "no" | "na"
  - "rationale": COMPREHENSIVE explanation that includes reasons for your decision, explicitly referencing the transcript context with exact timestamps. List all supporting evidence points and all issues/omissions found, each with their timestamps. **CRITICAL**: Your rationale MUST explicitly explain how each piece of evidence cited in "evidence_snippet" supports your decision. Every evidence snippet must be referenced and explained in the rationale.
  - "evidence_snippet": ALL relevant direct quotes or close paraphrases from the transcript that DIRECTLY support your rationale, each with exact timestamps in format [MM:SS - MM:SS] or [MM:SS]. **CRITICAL**: Only include evidence that is directly relevant to this specific parameter and that supports your answer. If multiple pieces of evidence exist, include all of them separated by semicolons. Format: "Quote 1 [0:02 - 0:06]; Quote 2 [1:12 - 1:24]; ...". Do NOT include evidence that contradicts your answer or is irrelevant to the parameter.


ONLY return the JSON object, no other text.
"""
    return prompt


def score_with_openai(
    transcript: str,
    rubric: Dict[str, Any],
    project_knowledge: Dict[str, Any],
    speaker_segments: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Use OpenAI to score transcript and return yes/no/na for each criterion.
    
    Args:
        transcript: The full transcript text
        rubric: The rubric dictionary loaded from YAML
        project_knowledge: Project knowledge dictionary for verification
        
    Returns:
        Dictionary with two keys:
            - "answers": mapping criterion IDs to "yes", "no", or "na"
            - "rationales": mapping criterion IDs to reasoning strings
    """
    if not OPENAI_API_KEY:
        raise ValueError("AZURE_KEY or OPENAI_API_KEY environment variable is not set")
    
    # Use Azure OpenAI endpoint if configured
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=AZURE_ENDPOINT
    )
    
    prompt = create_scoring_prompt(transcript, rubric, project_knowledge, speaker_segments)
    
    logger.info(f"Calling OpenAI API with model: {OPENAI_MODEL}")
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert call quality auditor. You evaluate call transcripts "
                        "against specific criteria and respond ONLY with a single JSON object. "
                        "CRITICAL: Always analyze the ENTIRE transcript from start to finish when scoring each parameter. "
                        "Check if customer requests were made earlier and whether the agent addressed them at any point in the conversation. "
                        "A customer repeating a request does not automatically mean the agent failed - check if the agent addressed it later. "
                        "EVIDENCE-REASONING ALIGNMENT: Every piece of evidence in 'evidence_snippet' MUST be explicitly referenced and explained in 'rationale'. "
                        "Only cite evidence that directly supports your answer and is relevant to the specific parameter. "
                        "Do not include evidence that contradicts your answer or is irrelevant. "
                        "Each key must be a criterion ID, and each value must be an object with "
                        "three fields: 'answer' (one of: yes, no, na), 'rationale' (COMPREHENSIVE explanation "
                        "including ALL reasons for your decision, with exact timestamps [MM:SS - MM:SS] "
                        "for every piece of evidence cited, and explicit explanation of how each evidence supports your decision), "
                        "and 'evidence_snippet' (ALL relevant direct quotes or close paraphrases from the transcript that DIRECTLY support "
                        "your rationale, each with exact timestamps in format [MM:SS - MM:SS] or [MM:SS], separated by semicolons if multiple, "
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent scoring
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        result_text = response.choices[0].message.content
        logger.info(f"OpenAI response received: {result_text[:200]}...")
        
        # Parse JSON response
        raw = json.loads(result_text)

        criterion_ids = {c['id'] for c in rubric['criteria']}

        answers: Dict[str, str] = {}
        rationales: Dict[str, str] = {}

        # Support both the new structured format and the previous simple mapping
        if all(isinstance(v, dict) for v in raw.values()):
            logger.info("Parsed structured scoring response with reasoning")
            for cid in criterion_ids:
                entry = raw.get(cid, {})
                if isinstance(entry, dict):
                    answer = str(entry.get("answer", "na")).lower()
                    rationale_parts = []
                    if entry.get("rationale"):
                        rationale_parts.append(str(entry["rationale"]).strip())
                    if entry.get("evidence_snippet"):
                        rationale_parts.append(f"Evidence: {str(entry['evidence_snippet']).strip()}")
                    rationale_text = " ".join(rationale_parts).strip()
                else:
                    # Fallback if entry is not a dict
                    answer = str(entry or "na").lower()
                    rationale_text = ""

                if answer not in ["yes", "no", "na"]:
                    logger.warning(f"Invalid answer '{answer}' for {cid}, defaulting to 'na'")
                    answer = "na"

                answers[cid] = answer
                rationales[cid] = rationale_text
        else:
            logger.info("Parsed legacy scoring response without structured reasoning")
            for cid in criterion_ids:
                value = raw.get(cid, "na")
                answer = str(value or "na").lower()
                if answer not in ["yes", "no", "na"]:
                    logger.warning(f"Invalid value '{answer}' for {cid}, defaulting to 'na'")
                    answer = "na"
                answers[cid] = answer
                rationales[cid] = ""

        # Fill any completely missing IDs
        missing_ids = criterion_ids - set(answers.keys())
        if missing_ids:
            logger.warning(f"Missing criterion IDs in response: {missing_ids}")
            for missing_id in missing_ids:
                answers[missing_id] = "na"
                rationales[missing_id] = ""

        logger.info(
            "Scoring completed. Yes: %d, No: %d, NA: %d",
            sum(1 for v in answers.values() if v == "yes"),
            sum(1 for v in answers.values() if v == "no"),
            sum(1 for v in answers.values() if v == "na"),
        )

        return {"answers": answers, "rationales": rationales}
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI JSON response: {e}")
        logger.error(f"Response was: {result_text}")
        raise ValueError(f"Invalid JSON response from OpenAI: {e}")
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise ValueError(f"OpenAI API error: {str(e)}")


def convert_yes_no_na_to_scores(
    yes_no_na_scores: Dict[str, str],
    rubric: Dict[str, Any],
    rationales: Dict[str, str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Convert yes/no/na responses to actual scores based on rubric.
    
    Args:
        yes_no_na_scores: Dictionary mapping criterion IDs to "yes", "no", or "na"
        rubric: The rubric dictionary
        
    Returns:
        List of criterion score dictionaries with points awarded
    """
    criteria_scores = []
    
    for criterion in rubric['criteria']:
        criterion_id = criterion['id']
        response = yes_no_na_scores.get(criterion_id, "na").lower()
        
        # Find matching level
        points_awarded = 0
        base_rationale = ""
        
        for level in criterion['levels']:
            if level['label'].lower() == response:
                points_awarded = level['points']
                base_rationale = f"Scored '{response.upper()}': {', '.join(level['descriptors'])}"
                break

        # Combine model-provided rationale (if any) with base rubric rationale
        model_reason = ""
        if rationales:
            model_reason = rationales.get(criterion_id, "").strip()

        if model_reason and base_rationale:
            rationale_text = f"{base_rationale}. {model_reason}"
        else:
            rationale_text = model_reason or base_rationale
        
        criteria_scores.append({
            "id": criterion_id,
            "name": criterion['name'],
            "max_points": criterion['max_points'],
            "points_awarded": points_awarded,
            "score": points_awarded,  # Alias for compatibility
            "response": response.upper(),  # YES, NO, or NA
            "rationale": rationale_text
        })
    
    return criteria_scores


def score_transcript(transcript_data: Dict[str, Any], rubric_path: str = None) -> Dict[str, Any]:
    """
    Score a transcript using OpenAI.
    
    Args:
        transcript_data: Dictionary containing transcription data
            Expected keys:
                - transcription: Full transcript text
                - speaker_segments: List of speaker segments with timing (optional, not used for scoring)
        rubric_path: Path to the rubric YAML file
        
    Returns:
        Dictionary with scoring results
    """
    logger.info("Starting transcript scoring with OpenAI")
    
    transcript = transcript_data.get("transcription", "")
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty or missing")
    
    logger.info(f"Transcript length: {len(transcript)} characters")
    
    # Load rubric and project knowledge (both Empire and HappiNest)
    rubric = load_rubric(rubric_path)
    project_knowledge = load_project_knowledge()
    
    logger.info(f"Loaded rubric with {len(rubric['criteria'])} criteria")

    speaker_segments = transcript_data.get("speaker_segments", [])
    
    # Get yes/no/na scores and rationales from OpenAI (with timing info)
    scoring_data = score_with_openai(transcript, rubric, project_knowledge, speaker_segments)
    yes_no_na_scores: Dict[str, str] = scoring_data.get("answers", {})
    rationales: Dict[str, str] = scoring_data.get("rationales", {})

    # Convert to actual scores
    criteria_scores = convert_yes_no_na_to_scores(yes_no_na_scores, rubric, rationales)
    
    # Calculate totals
    total_points = rubric.get('total_points', 100)
    total_score = sum(c['points_awarded'] for c in criteria_scores)
    percentage = round((total_score / total_points) * 100, 2) if total_points > 0 else 0
    
    logger.info(f"Scoring complete: {total_score}/{total_points} ({percentage}%)")
    
    return {
        "rubric_title": rubric.get("title", "Call Quality Rubric"),
        "total_points": total_points,
        "total_score": total_score,
        "percentage": percentage,
        "criteria_scores": criteria_scores,
        "yes_no_na_responses": yes_no_na_scores,  # Include raw yes/no/na for reference
        "metadata": {
            "model_used": OPENAI_MODEL,
            "transcript_length": len(transcript),
            "num_segments": len(transcript_data.get("speaker_segments", []))
        }
    }
