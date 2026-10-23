"""
LLM service: generates QA test cases from document selections.

Design decisions:
- Provider: Groq (free-tier) with llama-3.1-70b, falling back to a mock
  if GROQ_API_KEY is not set. Any other provider can be swapped in.
- Structured output: we request JSON via prompt engineering + JSON mode.
- Retry strategy: up to 3 attempts with exponential backoff. If all fail,
  we return a structured error response (not a 500).
- Duplicate policy: if the same selection_id is submitted again and
  force_regenerate=False, we return the existing generation. This is
  intentional — regenerating from the same text would produce different
  results each time, creating traceability ambiguity.
- Malformed LLM response: if the response cannot be parsed as JSON matching
  the TestCase schema, we store the raw response and return a partial
  GenerationOut with test_cases=[] and a parse_error field. "It usually works"
  is not a design.
"""
import json
import os
import re
import time
from typing import List, Optional

from app.schemas import TestCase


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.5  # seconds


SYSTEM_PROMPT = """You are a QA engineer generating test cases for a medical device (a home blood pressure monitor called the CardioTrack CT-200). 

Given relevant sections from the device manual, generate 3-5 concrete, executable QA test cases. Each test case must be:
- Specific enough that a different engineer could execute it without asking questions
- Directly traceable to the provided text (reference the section in section_reference)
- Focused on safety-critical behaviour where possible

Respond ONLY with a valid JSON object in this exact structure:
{
  "test_cases": [
    {
      "id": "TC-001",
      "title": "Short descriptive title",
      "preconditions": ["list of preconditions"],
      "steps": ["numbered steps"],
      "expected_result": "what should happen",
      "section_reference": "e.g. Section 3.1 Pressure Safety"
    }
  ]
}

Do not include any text outside the JSON object. Do not include markdown code fences."""


def _call_groq(user_content: str) -> str:
    """Call Groq API. Returns raw response string."""
    import httpx

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _call_mock(user_content: str) -> str:
    """
    Mock LLM for when GROQ_API_KEY is absent.
    Generates basic test cases based on keywords in the content.
    """
    # Detect section references
    section_refs = re.findall(r"\d+\.\d+\s+\w[\w\s]{0,30}", user_content)
    ref = section_refs[0].strip() if section_refs else "Section provided"

    test_cases = [
        {
            "id": "TC-001",
            "title": "Verify normal measurement cycle completes successfully",
            "preconditions": [
                "Device is fully charged (>50%)",
                "Standard adult cuff is properly connected",
                "Test subject rested for 5 minutes",
            ],
            "steps": [
                "Place cuff on bare upper arm 2-3 cm above elbow crease",
                "Press START/STOP button",
                "Remain still until measurement completes",
                "Record displayed SYS, DIA, PR values",
            ],
            "expected_result": "Device displays SYS/DIA (mmHg) and PR (bpm) values within 60 seconds without error codes.",
            "section_reference": ref,
        },
        {
            "id": "TC-002",
            "title": "Verify E3 error on pressure exceeding safe threshold",
            "preconditions": [
                "Device connected to test bench pressure source",
                "Firmware debug mode enabled",
            ],
            "steps": [
                "Simulate cuff pressure ramping beyond the software threshold (295 mmHg for v1 / 290 mmHg for v2)",
                "Observe device display",
                "Measure time from threshold detection to full deflation",
                "Check non-volatile event log",
            ],
            "expected_result": "Device displays E3 error code, deflates to 0 mmHg within the specified window (2 s for v1, 1.5 s for v2), and logs a timestamped event.",
            "section_reference": "Section 3.1 Pressure Safety",
        },
        {
            "id": "TC-003",
            "title": "Verify E4 low-battery warning at 5% charge",
            "preconditions": [
                "Device battery discharged to exactly 5% using discharge jig",
            ],
            "steps": [
                "Power on device",
                "Observe display",
                "Attempt one measurement",
                "Observe behaviour on second measurement attempt",
            ],
            "expected_result": "E4 warning displayed on power-on. Device allows exactly one measurement then refuses further measurements until charged.",
            "section_reference": "Section 3.4 Alarm Conditions",
        },
        {
            "id": "TC-004",
            "title": "Verify memory does not overwrite data until capacity reached",
            "preconditions": [
                "User profile memory cleared",
            ],
            "steps": [
                "Perform measurements until internal memory is full (60 for v1, 90 for v2)",
                "Perform one additional measurement",
                "Inspect stored readings",
            ],
            "expected_result": "After reaching capacity, the oldest reading is overwritten (circular buffer). Total stored count does not exceed the stated limit.",
            "section_reference": "Section 6.1 Local Storage",
        },
    ]

    return json.dumps({"test_cases": test_cases})


def _parse_llm_response(raw: str) -> tuple[List[TestCase], str | None]:
    """
    Parse LLM response into TestCase objects.
    Returns (test_cases, parse_error).
    parse_error is None on success.
    """
    try:
        # Strip potential markdown fences
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        data = json.loads(cleaned)
        raw_cases = data.get("test_cases", [])

        if not isinstance(raw_cases, list):
            return [], f"'test_cases' is not a list: {type(raw_cases)}"

        test_cases = []
        for i, tc in enumerate(raw_cases):
            try:
                test_cases.append(TestCase(
                    id=tc.get("id", f"TC-{i+1:03d}"),
                    title=tc.get("title", "Untitled"),
                    preconditions=tc.get("preconditions", []),
                    steps=tc.get("steps", []),
                    expected_result=tc.get("expected_result", ""),
                    section_reference=tc.get("section_reference", ""),
                ))
            except Exception as e:
                return [], f"TestCase #{i} validation error: {e}"

        if not test_cases:
            return [], "LLM returned an empty test_cases list"

        return test_cases, None

    except json.JSONDecodeError as e:
        return [], f"JSON parse error: {e}. Raw (first 300 chars): {raw[:300]}"
    except Exception as e:
        return [], f"Unexpected parse error: {e}"


def generate_test_cases(
    context_text: str,
    node_ids: List[int],
) -> dict:
    """
    Call LLM (or mock) to generate test cases.
    Returns a dict with keys: test_cases, prompt_used, raw_llm_response, parse_error.

    Retry logic: 3 attempts, exponential backoff.
    On all failures: returns parse_error with empty test_cases.
    """
    user_content = (
        "Please generate QA test cases for the following sections from the "
        "CardioTrack CT-200 manual:\n\n"
        f"{context_text}\n\n"
        "Remember: respond ONLY with the JSON object."
    )

    raw_response = ""
    parse_error: Optional[str] = None
    test_cases: List[TestCase] = []

    caller = _call_groq if GROQ_API_KEY else _call_mock

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw_response = caller(user_content)
            test_cases, parse_error = _parse_llm_response(raw_response)
            if parse_error is None:
                break
            # If parse failed, retry (maybe the model gave partial output)
            print(f"[LLM] Attempt {attempt} parse error: {parse_error}")
        except Exception as e:
            parse_error = f"API call failed on attempt {attempt}: {e}"
            print(f"[LLM] {parse_error}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))

    return {
        "test_cases": test_cases,
        "prompt_used": SYSTEM_PROMPT,
        "raw_llm_response": raw_response,
        "parse_error": parse_error,
        "node_ids": node_ids,
    }
