from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import logging
import json
from dotenv import load_dotenv
from openai_client import get_openai_client
from typing import Optional, List

load_dotenv()

client = get_openai_client()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Repair DIY AI Backend",
    description="Backend API for Repair DIY AI application",
    version="1.0.0",
)

#  CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORY_PROMPTS = {
    "appliance": {
        "name": "Appliance Repair",
        "expert_persona": "Expert home appliance repair technician with 20+ years of experience",
        "focus": "Common household appliances like refrigerators, washing machines, dryers, dishwashers, and ovens",
        "emphasis": "Technical details and practical homeowner solutions",
        "safety_note": "Always unplug appliances before any repair work and check for gas connections on gas appliances",
        "prompt_template": "As an expert home appliance repair technician with 20+ years of experience, generate 1 practical question-answer pair for {category} repair. Focus on technical details and practical homeowner solutions. Include specific model considerations when relevant. Format as Q: [question] A: [answer]",
    },
    "plumbing": {
        "name": "Plumbing Repair",
        "expert_persona": "Professional plumber with extensive residential experience",
        "focus": "Common plumbing issues like leaks, clogs, fixture repairs, and pipe problems",
        "emphasis": "Safety for homeowner attempts and realistic solutions",
        "safety_note": "Always turn off water supply before any plumbing work and know when to call a professional",
        "prompt_template": "As a professional plumber with extensive residential experience, generate 1 practical question-answer pair for {category} repair. Focus on safety for homeowner attempts and realistic solutions. Include when to call a professional plumber. Format as Q: [question] A: [answer]",
    },
    "electrical": {
        "name": "Electrical Repair",
        "expert_persona": "Licensed electrician specializing in safe home electrical repairs",
        "focus": "SAFE homeowner-level electrical work like outlet replacement, switch repair, and light fixture installation",
        "emphasis": "Critical safety warnings and when to call professionals",
        "safety_note": "ALWAYS turn off power at the breaker before any electrical work and test with a multimeter",
        "prompt_template": "As a licensed electrician specializing in safe home electrical repairs, generate 1 practical question-answer pair for {category} repair. Focus on critical safety warnings and when to call professionals. Emphasize electrical safety procedures. Format as Q: [question] A: [answer]",
    },
    "hvac": {
        "name": "HVAC Maintenance",
        "expert_persona": "HVAC technician specializing in homeowner maintenance",
        "focus": "Basic HVAC maintenance and troubleshooting like filter changes, thermostat issues, and vent cleaning",
        "emphasis": "Seasonal considerations and maintenance best practices",
        "safety_note": "Turn off power to HVAC units before maintenance and be cautious with refrigerant lines",
        "prompt_template": "As an HVAC technician specializing in homeowner maintenance, generate 1 practical question-answer pair for {category} maintenance. Focus on seasonal considerations and maintenance best practices. Include energy efficiency tips. Format as Q: [question] A: [answer]",
    },
    "general": {
        "name": "General Home Repair",
        "expert_persona": "Skilled handyperson with general home repair expertise",
        "focus": "Common general repairs like drywall repair, door/window problems, flooring issues, and basic carpentry",
        "emphasis": "Material specifications and practical DIY solutions",
        "safety_note": "Use appropriate safety equipment and tools for each type of repair",
        "prompt_template": "As a skilled handyperson with general home repair expertise, generate 1 practical question-answer pair for {category} repair. Focus on material specifications and practical DIY solutions. Include tool recommendations when relevant. Format as Q: [question] A: [answer]",
    },
    "random": {
        "name": "Random Repair",
        "expert_persona": "Experienced home repair specialist with broad knowledge across all repair categories",
        "focus": "Various home repair topics across all categories",
        "emphasis": "Practical solutions and safety considerations",
        "safety_note": "Always prioritize safety and know your limitations",
        "prompt_template": "As an experienced home repair specialist with broad knowledge, generate 1 practical question-answer pair for a random {category} repair topic. Focus on practical solutions and safety considerations. Format as Q: [question] A: [answer]",
    },
}


class HealthResponse(BaseModel):
    status: str
    message: str


class GenerateRequest(BaseModel):
    category: str


class GenerateResponse(BaseModel):
    content: str


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="success", message="Repair DIY AI Backend is running")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="success", message="Backend is healthy")


def stream_text(messages, protocol: str = "data"):
    stream = client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo",
        stream=True,
    )

    # When protocol is set to "text", you will send a stream of plain text chunks
    # https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#text-stream-protocol
    if protocol == "text":
        for chunk in stream:
            for choice in chunk.choices:
                if choice.finish_reason == "stop":
                    break
                else:
                    yield "{text}".format(text=choice.delta.content)

    # When protocol is set to "data", you will send a stream data part chunks
    # https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol
    elif protocol == "data":

        for chunk in stream:
            for choice in chunk.choices:
                if choice.finish_reason == "stop":
                    continue

                else:
                    res = "0:{text}\n".format(text=json.dumps(choice.delta.content))
                    yield res

            if chunk.choices == []:
                usage = chunk.usage
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens

                res = 'd:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}}}}\n'.format(
                    reason="stop", prompt=prompt_tokens, completion=completion_tokens
                )
                yield res


@app.post("/generate")
async def generate_qa_pairs(request: GenerateRequest):
    logger.debug(f"Received generate request for category: {request.category}")

    category_config = CATEGORY_PROMPTS.get(request.category, CATEGORY_PROMPTS["random"])

    logger.debug(f"Category config: {category_config}")

    json_example = """
    [
        {
            "question": "...",
            "answer": "...",
            "equipment_problem": "...",
            "tools_required": ["..."],
            "steps": ["..."],
            "safety_info": "...",
            "tips": "..."
        }
    ]
    """

    user_prompt = f"""
    Generate 2 random repair Q&A samples.
    Each must use a different persona from the system-defined list.
    """

    system_prompt = f"""
    You are {category_config['expert_persona']}. 
        
    Your expertise focuses on: {category_config['focus']}
    Your emphasis is on: {category_config['emphasis']}

    IMPORTANT SAFETY NOTE: {category_config['safety_note']}

    Your goal is to produce synthetic Q&A data with JSON format. 
    The JSON format should be like this and return ONLY this json no any other explanations.
    
    {json_example}

    All templates produce the same JSON structure with 7 required fields. 
    Keep question and answer concise maximum 2 sentences. Other fields should be 1 line.

    Guidelines:
    Realistic Scenarios: Focus on common, real-world repair situations
    Equipment-Specific: Use specific equipment names and problems
    Step-by-Step: Provide clear, detailed steps
    Safety-First: Include important safety information
    Tips & Tricks: Offer practical tips and advice
    Variety: Use different equipment types and problems
    """

    logger.debug(f"System prompt: {system_prompt}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = StreamingResponse(stream_text(messages, protocol="text"))
    response.headers["x-vercel-ai-data-stream"] = "v1"
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
