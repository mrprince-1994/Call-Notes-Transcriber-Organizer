"""Detects AWS AI/ML questions in live transcript text.

Watches for questions mentioning AWS AI/ML services and triggers
the AgentCore agent to generate answers.
"""
import re

# AWS AI/ML service keywords to watch for
AWS_AIML_KEYWORDS = [
    r"sagemaker",
    r"sage\s*maker",
    r"bedrock",
    r"agentcore",
    r"agent\s*core",
    r"quicksight",
    r"quick\s*sight",
    r"amazon\s*q\b",
    r"comprehend",
    r"rekognition",
    r"textract",
    r"transcribe",
    r"polly",
    r"kendra",
    r"personalize",
    r"trainium",
    r"inferentia",
    r"codewhisperer",
    r"code\s*whisperer",
    r"titan",
    r"anthropic",
    r"claude",
    r"foundation\s*model",
    r"guardrail",
    r"knowledge\s*base",
    r"rag\b",
    r"retrieval\s*augmented",
    r"fine[\s\-]*tun",
    r"prompt\s*engineering",
    r"generative\s*ai",
    r"gen\s*ai",
    r"machine\s*learning",
    r"deep\s*learning",
    r"neural\s*network",
    r"ai\s*service",
    r"ml\s*service",
]

# Question indicators
QUESTION_PATTERNS = [
    r"\bwhat\s+(is|are|does|do|can|could|would|should)\b",
    r"\bhow\s+(does|do|can|could|would|should|is|are|to|much|many)\b",
    r"\bwhy\s+(does|do|is|are|would|should|can)\b",
    r"\bcan\s+(you|we|it|they|i)\b",
    r"\bcould\s+(you|we|it|they|i)\b",
    r"\bis\s+(it|there|that|this)\b",
    r"\bare\s+(there|they|these|those)\b",
    r"\bdo\s+(you|we|they)\b",
    r"\bdoes\s+(it|that|this)\b",
    r"\btell\s+me\s+about\b",
    r"\bexplain\b",
    r"\bdescribe\b",
    r"\bwhat's\b",
    r"\bhow's\b",
    r"\?",
]

_keyword_pattern = re.compile("|".join(AWS_AIML_KEYWORDS), re.IGNORECASE)
_question_pattern = re.compile("|".join(QUESTION_PATTERNS), re.IGNORECASE)


def is_aws_aiml_question(text: str) -> bool:
    """Check if text contains an AWS AI/ML question.

    Returns True if the text mentions an AWS AI/ML keyword AND
    appears to be a question.
    """
    if not text or len(text) < 15:
        return False

    has_keyword = bool(_keyword_pattern.search(text))
    has_question = bool(_question_pattern.search(text))

    return has_keyword and has_question


def extract_question(text: str) -> str:
    """Extract the most relevant question from a transcript line.

    If the text contains a question mark, extract the sentence containing it.
    Otherwise return the full text as the question.
    """
    if "?" in text:
        # Find the sentence ending with ?
        sentences = re.split(r"(?<=[.!])\s+", text)
        for sentence in sentences:
            if "?" in sentence and _keyword_pattern.search(sentence):
                return sentence.strip()

    return text.strip()
