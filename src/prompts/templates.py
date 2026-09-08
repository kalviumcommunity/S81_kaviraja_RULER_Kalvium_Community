class PromptTemplate:
    """
    A simple wrapper around a string template to allow named placeholder formatting.
    """
    def __init__(self, template: str):
        self.template = template

    def render(self, **kwargs) -> str:
        """
        Inject dynamic values into the template.
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")

# Predefined templates
RAG_SYSTEM_PROMPT = PromptTemplate(
    "You are a helpful {role} specialized AI assistant."
)

RAG_USER_PROMPT = PromptTemplate(
    "Explain what {topic} is in {length} concise sentences."
)

# Grounded RAG Generation Templates (Tasks 1 to 5)
RAG_GROUNDED_SYSTEM_PROMPT = PromptTemplate(
    "You are a strict, grounded AI assistant for a financial regulatory compliance system.\n"
    "Your objective is to answer user queries using ONLY the injected context provided in the prompt.\n"
    "Rules:\n"
    "1. Base your answer strictly on the provided context chunks. Do not introduce outside facts or speculate.\n"
    "2. If the context does not contain sufficient information to answer the question, state clearly: "
    "'I do not have enough information in the provided context to answer this question.'\n"
    "3. Cite the relevant source chunks (e.g. [Chunk ID]) supporting your answer.\n"
    "4. Maintain complete factual fidelity to the context."
)

RAG_GROUNDED_USER_PROMPT = PromptTemplate(
    "CONTEXT INFORMATION:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n\n"
    "QUESTION: {query}\n\n"
    "Please provide a grounded answer based strictly on the context above, citing the supporting chunk IDs:"
)

RAG_UNGROUNDED_USER_PROMPT = PromptTemplate(
    "QUESTION: {query}\n\n"
    "Please answer the question based on your general knowledge:"
)

