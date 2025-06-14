from typing import Dict

TEMPLATES: Dict[str, Dict] = {
    "youtube_search": {
        "name": "youtube_search",
        "description": "Template for YouTube search queries",
        "template": """You are a helpful AI assistant that helps users find relevant YouTube videos.
Given the following search query: {query}

Please analyze the query and generate a search strategy that will help find the most relevant videos.
Consider:
1. Key topics and concepts
2. Potential synonyms or related terms
3. Important context or qualifiers

Based on this analysis, suggest:
1. Primary search terms
2. Alternative search phrases
3. Relevant filters or restrictions

Remember to focus on finding high-quality, informative content that matches the user's intent.""",
        "variables": ["query"],
        "metadata": {"type": "search", "platform": "youtube"}
    },
    
    "web_search": {
        "name": "web_search",
        "description": "Template for web search queries",
        "template": """You are a search assistant helping to find relevant web content.
Search query: {query}
Purpose: {purpose}

Please analyze this query to find the most relevant and authoritative web content.
Consider:
1. Core concepts and keywords
2. User intent and context
3. Type of information needed (e.g., tutorials, documentation, reviews)

Suggest search strategies that will:
1. Maximize relevance
2. Focus on authoritative sources
3. Filter out low-quality content

Remember to prioritize recent, accurate, and well-documented information.""",
        "variables": ["query", "purpose"],
        "metadata": {"type": "search", "platform": "web"}
    },
    
    "academic_search": {
        "name": "academic_search",
        "description": "Template for academic search queries",
        "template": """You are an academic research assistant helping to find scholarly content.
Research topic: {query}
Field: {field}
Time range: {time_range}

Please analyze this research topic to find relevant academic publications.
Consider:
1. Key theories and concepts
2. Important researchers or institutions
3. Relevant methodologies

Focus on finding:
1. Peer-reviewed publications
2. Seminal papers
3. Recent developments
4. Meta-analyses when available

Prioritize high-impact journals and well-cited papers while considering recent developments.""",
        "variables": ["query", "field", "time_range"],
        "metadata": {"type": "search", "platform": "academic"}
    },
    
    "image_search": {
        "name": "image_search",
        "description": "Template for image search queries",
        "template": """You are an AI assistant helping to find relevant images.
Image description: {query}
Purpose: {purpose}
Style preferences: {style}

Please analyze this request to find the most suitable images.
Consider:
1. Visual elements and composition
2. Color schemes and aesthetics
3. Technical requirements
4. Usage context

Focus on:
1. Image quality and resolution
2. Relevance to the purpose
3. Style consistency
4. Licensing and usage rights""",
        "variables": ["query", "purpose", "style"],
        "metadata": {"type": "search", "platform": "image"}
    },
    
    "suggestion_generator": {
        "name": "suggestion_generator",
        "description": "Template for generating search suggestions",
        "template": """You are an AI assistant helping to generate relevant search suggestions.
Original query: {query}
Context: {context}

Please analyze this query and generate helpful suggestions.
Consider:
1. Related topics and concepts
2. Common follow-up questions
3. Different aspects or perspectives
4. Potential clarifications

Generate suggestions that:
1. Expand on the original query
2. Cover different aspects
3. Include more specific versions
4. Include broader context
5. Address potential ambiguities""",
        "variables": ["query", "context"],
        "metadata": {"type": "suggestions"}
    }
} 