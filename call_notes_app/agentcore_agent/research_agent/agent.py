"""AgentCore Runtime — Customer Research Agent (streaming).

Built with Strands. Uses DuckDuckGo web search to research customers,
find news, funding rounds, tech stack, and competitive context.
Streams results back via SSE.

Payload schema:
  {
    "prompt": "<research question or customer name>",
    "customer": "<optional customer name hint>"
  }
"""
import os
import json
import re
import urllib.request
import urllib.parse

os.environ["BYPASS_TOOL_CONSENT"] = "true"

from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp

SONNET_MODEL_ID = "us.anthropic.claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an expert customer research analyst helping an AWS account manager \
prepare for and follow up on customer calls. Your job is to produce a comprehensive \
business brief that the account manager can use to have an informed, value-driven conversation.

You have a `web_search` tool. Use it aggressively — run 4-6 targeted searches to build \
a thorough picture. Search for the company name, their products, recent news, AI/ML \
initiatives, competitors, and industry trends.

Structure your research brief with these exact sections:

## 1. Business Overview
- What the company does, their core products/services, and primary focus areas
- Industry vertical, company size, stage (startup/growth/enterprise), headquarters
- Key customers, partners, or market segments they serve
- Recent funding, acquisitions, leadership changes, or strategic pivots

## 2. AI/ML Solutions in Production
- Search specifically for any AI, ML, generative AI, or automation capabilities \
the company has shipped or announced
- Look for press releases, blog posts, or product pages mentioning AI/ML features
- Note which models, platforms, or cloud providers they use if mentioned
- If no AI/ML solutions are found, state that clearly — don't fabricate

## 3. AI/ML Use Cases & Industry Success Stories
- Based on the company's industry vertical, identify 3-5 high-impact AI/ML use cases \
that similar companies have successfully deployed
- Reference real AWS customer success stories or case studies in the same vertical \
(e.g., "Company X in [industry] used Amazon Bedrock for [use case]")
- Prioritize use cases that align with the company's business model and pain points
- Include specific AWS services that map to each use case (Bedrock, SageMaker, \
Textract, Comprehend, Personalize, etc.)

## 4. Recommended Talking Points
- 4-6 specific, actionable talking points the account manager should raise
- Frame each as a question or conversation starter tied to a business outcome
- Connect each talking point to a specific AWS capability or service
- Include at least one point about generative AI / Amazon Bedrock
- Tailor to the company's maturity level — don't pitch advanced ML to a company \
that hasn't started their cloud journey

Always cite your sources with URLs. If search returns limited results for any section, \
say so clearly and provide your best analysis based on available information."""

app = BedrockAgentCoreApp()


def _clean_html(s: str) -> str:
    """Strip HTML tags and decode common entities."""
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    return s.strip()


def _ddg_html_search(query: str, max_results: int = 5) -> list[dict]:
    """Fallback: scrape DuckDuckGo HTML results."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    results = []
    blocks = re.findall(r"result__body.*?(?=result__body|$)", html, re.DOTALL)
    for block in blocks[:max_results]:
        title_m = re.search(r'result__a[^>]*>(.*?)</a>', block, re.DOTALL)
        url_m   = re.search(r'result__url[^>]*>\s*(.*?)\s*</span>', block, re.DOTALL)
        snip_m  = re.search(r'result__snippet[^>]*>(.*?)</span>', block, re.DOTALL)
        title = _clean_html(title_m.group(1)) if title_m else ""
        link  = _clean_html(url_m.group(1))   if url_m   else ""
        snip  = _clean_html(snip_m.group(1))  if snip_m  else ""
        if title or snip:
            results.append({"title": title, "href": link, "body": snip})
    return results


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo for current information about a company or topic.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default 5)
    """
    results = []

    # Primary: ddgs package (formerly duckduckgo-search)
    try:
        from ddgs import DDGS as DDGS_New
        with DDGS_New() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
        results = hits
    except ImportError:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=max_results))
            results = hits
        except Exception:
            pass
    except Exception:
        pass

    # Fallback: HTML scraper if no results from package
    if not results:
        try:
            results = _ddg_html_search(query, max_results)
        except Exception as e2:
            return f"Search error: {e2}"

    if not results:
        return f"No results found for: {query}"

    parts = []
    for r in results:
        title = r.get("title", "")
        link  = r.get("href", r.get("url", ""))
        body  = r.get("body", r.get("snippet", ""))
        parts.append(f"**{title}**\n{link}\n{body}")

    return f"Search results for '{query}':\n\n" + "\n\n---\n\n".join(parts)


@app.entrypoint
async def research_customer(payload, context):
    question = payload.get("prompt", "")
    customer_hint = payload.get("customer", "")

    if not question:
        yield {"text": "No research question provided.", "type": "error"}
        return

    # Prepend customer context if provided
    full_prompt = question
    if customer_hint and customer_hint.lower() not in question.lower():
        full_prompt = f"Research customer: {customer_hint}\n\n{question}"

    try:
        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            tools=[web_search],
            model=SONNET_MODEL_ID,
            callback_handler=None,
        )

        stream = agent.stream_async(full_prompt)
        async for event in stream:
            yield event

    except Exception as e:
        yield {"text": f"Error: {e}", "type": "error"}


if __name__ == "__main__":
    app.run()
