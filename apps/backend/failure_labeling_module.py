from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import re
import logging
from openai_client import get_openai_client

logger = logging.getLogger(__name__)
client = get_openai_client()

# Router for failure labeling endpoints
failure_labeling_router = APIRouter()

# Failure modes configuration
FAILURE_MODES = {
    "incomplete_answer": "Incomplete Answer",
    "safety_violations": "Safety Violations",
    "unrealistic_tools": "Unrealistic Tools",
    "overcomplicated_solution": "Overcomplicated Solution",
    "missing_context": "Missing Context",
    "poor_quality_tips": "Poor Quality Tips"
}

class FailureLabelingRequest(BaseModel):
    data: List[Dict[str, Any]]
    auto_label: bool = True

class FailureLabelingResponse(BaseModel):
    success: bool
    message: str
    df_json: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None


class ManualLabelingRequest(BaseModel):
    trace_id: str
    labels: Dict[str, int]  # failure_mode: 0 or 1


def create_failure_dataframe(qa_data: List[Dict[str, Any]]) -> pd.DataFrame:
    df_data = []

    for i, item in enumerate(qa_data):
        row = {
            'trace_id': f"trace_{i + 1:03d}",
            'question': item.get('question', ''),
            'answer': item.get('answer', ''),
            'equipment_problem': item.get('equipment_problem', ''),
            'tools_required': json.dumps(item.get('tools_required', [])),
            'steps': json.dumps(item.get('steps', [])),
            'safety_info': item.get('safety_info', ''),
            'tips': item.get('tips', ''),
        }

        # Add binary columns for each failure mode (initially 0 = success)
        for mode in FAILURE_MODES.keys():
            row[f'{mode}'] = 0

        df_data.append(row)

    df = pd.DataFrame(df_data)
    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    return df


def llm_auto_label(qa_item: Dict[str, Any]) -> Dict[str, int]:
    system_prompt = f"""
    You are an expert quality assessor for DIY repair Q&A content. 
    Analyze the provided Q&A item and identify any of these failure modes:
    
    1. incomplete_answer: Answer is too brief, missing key steps, or doesn't fully address the question
    2. safety_violations: Missing critical safety warnings, incorrect safety advice, or dangerous recommendations
    3. unrealistic_tools: Lists tools that are too specialized, expensive, or not commonly available to homeowners
    4. overcomplicated_solution: Solution is unnecessarily complex when simpler alternatives exist
    5. missing_context: Lacks important context like when to call a professional, skill level required, etc.
    6. poor_quality_tips: Tips are generic, unhelpful, or don't add practical value
    
    For each failure mode, respond with 1 if the issue is present, 0 if it's not.
    Be strict but fair in your assessment.
    
    Respond with ONLY a JSON object in this exact format:
    {{
        "incomplete_answer": 0 or 1,
        "safety_violations": 0 or 1,
        "unrealistic_tools": 0 or 1,
        "overcomplicated_solution": 0 or 1,
        "missing_context": 0 or 1,
        "poor_quality_tips": 0 or 1
    }}
    """

    user_prompt = f"""
    Analyze this Q&A item:
    
    Question: {qa_item.get('question', '')}
    Answer: {qa_item.get('answer', '')}
    Equipment Problem: {qa_item.get('equipment_problem', '')}
    Tools Required: {qa_item.get('tools_required', [])}
    Steps: {qa_item.get('steps', [])}
    Safety Info: {qa_item.get('safety_info', '')}
    Tips: {qa_item.get('tips', '')}
    
    Identify any failure modes and respond with the JSON format specified.
    """

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()
        labels = json.loads(result_text)
        return labels

    except Exception as e:
        logger.error(f"Error in LLM auto-labeling: {e}")
        # Return all zeros if there's an error
        return {mode: 0 for mode in FAILURE_MODES.keys()}


def get_failure_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a summary of failure modes in the dataset."""
    summary = {
        "total_items": len(df),
        "failure_counts": {},
        "failure_rates": {},
        "most_common_failures": []
    }

    for mode in FAILURE_MODES.keys():
        count = df[mode].sum()
        rate = count / len(df) if len(df) > 0 else 0
        summary["failure_counts"][mode] = int(count)
        summary["failure_rates"][mode] = round(rate, 3)

    failure_counts = [(mode, summary["failure_counts"][mode]) for mode in FAILURE_MODES.keys()]
    failure_counts.sort(key=lambda x: x[1], reverse=True)
    summary["most_common_failures"] = failure_counts[:3]

    return summary


@failure_labeling_router.post("/failure-labeling", response_model=FailureLabelingResponse)
async def create_failure_labels(request: FailureLabelingRequest):
    """
    Create failure labels for Q&A data using LLM auto-labeling.
    """
    logger.debug(f"Received failure labeling request for {len(request.data)} items")

    try:
        # Create initial DataFrame
        df = create_failure_dataframe(request.data)

        if request.auto_label:
            # Auto-label using LLM
            logger.info("Starting LLM auto-labeling...")
            for i, item in enumerate(request.data):
                labels = llm_auto_label(item)

                # Update the DataFrame with labels
                for mode, label in labels.items():
                    df.at[i, mode] = label

            logger.info("Auto-labeling completed")

        # Generate summary
        summary = get_failure_summary(df)

        # Convert DataFrame to JSON for response
        df_json = df.to_json(orient='records')

        return FailureLabelingResponse(
            success=True,
            message=f"Successfully labeled {len(df)} items",
            df_json=df_json,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Error in failure labeling: {e}")
        return FailureLabelingResponse(
            success=False,
            message=f"Error: {str(e)}"
        )
