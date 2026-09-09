class PromptTemplate:
    """
    A simple wrapper around a string template to allow named placeholder formatting.
    """
    def __init__(self, template: str, default_kwargs: dict = None):
        self.template = template
        self.default_kwargs = default_kwargs or {}

    def render(self, **kwargs) -> str:
        """
        Inject dynamic values into the template with flexible placeholder aliasing.
        """
        merged = {**self.default_kwargs, **kwargs}
        if "context_str" in merged and "context" not in merged:
            merged["context"] = merged["context_str"]
        elif "context" in merged and "context_str" not in merged:
            merged["context_str"] = merged["context"]

        if "query" in merged and "question" not in merged:
            merged["question"] = merged["query"]
        elif "question" in merged and "query" not in merged:
            merged["query"] = merged["question"]

        try:
            return self.template.format(**merged)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")

# Predefined templates
RAG_SYSTEM_PROMPT = PromptTemplate(
    "You are a helpful {role} specialized AI assistant.",
    default_kwargs={"role": "RAG"}
)
#explain me the funtion
RAG_USER_PROMPT = PromptTemplate(
    "Explain what {topic} is in {length} concise sentences."
)

# Task 4 & Task 1: Strict Grounding & Context-Injection Prompt Templates
GROUNDING_INSTRUCTIONS = (
    "GROUNDING RULES:\n"
    "1. Answer the user's question ONLY using the factual information provided in the [CONTEXT] section below.\n"
    "2. Do NOT assume, extrapolate, or invent facts outside the provided context.\n"
    "3. Cite your sources using the chunk markers (e.g. [1], [2], or [Source X]) whenever stating a factual claim.\n"
    "4. If the provided context is insufficient or does not contain the answer, you MUST explicitly state: "
    "\"The provided context does not contain sufficient information to answer this question.\" Do not attempt to guess."
)

RAG_GROUNDED_SYSTEM_PROMPT = PromptTemplate(
    "You are an expert AI assistant specialized in {role}.\n\n"
    f"{GROUNDING_INSTRUCTIONS}",
    default_kwargs={"role": "Banking Regulation & Financial Compliance"}
)

RAG_CONTEXT_INJECTION_USER_PROMPT = PromptTemplate(
    "[CONTEXT]\n"
    "{context}\n\n"
    "[QUESTION]\n"
    "{question}\n\n"
    "[ANSWER]"
)

# Aliases for grounded generator
RAG_GROUNDED_USER_PROMPT = PromptTemplate(
    "[CONTEXT]\n"
    "{context_str}\n\n"
    "[QUESTION]\n"
    "{query}\n\n"
    "[ANSWER]"
)

RAG_UNGROUNDED_USER_PROMPT = PromptTemplate(
    "[QUESTION]\n"
    "{query}\n\n"
    "[ANSWER]"
)# Task 2: Conversational Query Rewriter Prompt Template
CONVERSATIONAL_QUERY_REWRITE_SYSTEM_PROMPT = (
    "You are an expert query reformulation assistant in a conversational Retrieval-Augmented Generation (RAG) system.\n"
    "Your role is to analyze a multi-turn conversation history and a user's latest follow-up question, "
    "and rewrite the follow-up question into a single, fully self-contained, standalone query that can be embedded "
    "and used for semantic document retrieval.\n\n"
    "REWRITING RULES:\n"
    "1. Identify coreference pronouns (e.g., 'it', 'they', 'them', 'this', 'that', 'these', 'its') and replace them "
    "with the specific entity, topic, or regulation discussed in the conversation history.\n"
    "2. If the question is elliptical or partial (e.g., 'And the threshold?', 'What about exceptions?'), expand it into a complete, clear question.\n"
    "3. If the user's question is ALREADY standalone and independent (does not reference or depend on prior history), return it VERBATIM without changes.\n"
    "4. Preserve the user's exact informational intent without adding extra speculative questions.\n"
    "5. Output ONLY the rewritten standalone question. Do NOT include explanations, prefixes, quotation marks, or conversational filler."
)

CONVERSATIONAL_QUERY_REWRITE_USER_PROMPT = PromptTemplate(
    "[CONVERSATION HISTORY]\n"
    "{chat_history}\n\n"
    "[FOLLOW-UP QUESTION]\n"
    "{question}\n\n"
    "[STANDALONE REWRITTEN QUERY]"
)

