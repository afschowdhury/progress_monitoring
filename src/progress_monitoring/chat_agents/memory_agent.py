import asyncio

from google.adk.agents import Agent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from pydantic import PrivateAttr

from progress_monitoring.memory_manager import MemoryManager


class MemoryAgent(Agent):
    """
    A multi-agent chat agent that answers questions based on its memory.
    Utilizes MemoryManager for storage/retrieval and ADK for reasoning.
    """

    _memory_manager: MemoryManager = PrivateAttr()

    def __init__(self, memory_file_path: str, **kwargs):
        super().__init__(
            name="memory_agent",
            model="gemini-2.0-flash",
            description="Agent that answers questions based on memory.",
            **kwargs,
        )
        self._memory_manager = MemoryManager(memory_file_path)

    async def run(self, context: InvocationContext) -> str:
        user_message = context.session.state.get("user_message", "")
        query = user_message if user_message else ""
        results = self._memory_manager.search_similar_reports(query, limit=3)
        if results:
            answer = f"Based on my memory, here is what I found:\n"
            for i, r in enumerate(results, 1):
                answer += f"{i}. {r.get('progress_summary', r.get('analysis_summary', 'No summary'))}\n"
        else:
            answer = "I could not find relevant information in my memory."
        return answer


class ProgressAgent(MemoryAgent):
    """Agent specialized in progress-related questions."""

    def __init__(self, memory_file_path: str, **kwargs):
        super().__init__(memory_file_path, **kwargs)
        self.name = "progress_agent"
        self.model = "gemini-2.0-flash"
        self.description = "Agent specialized in progress-related questions."

    async def run(self, context: InvocationContext) -> str:
        user_message = context.session.state.get("user_message", "")
        query = user_message if user_message else ""
        # Focus on progress reports
        results = self._memory_manager.search_similar_reports(
            query, limit=3, record_type="progress_report"
        )
        if results:
            answer = f"[Progress Expert]\n"
            for i, r in enumerate(results, 1):
                answer += f"{i}. {r.get('progress_summary', 'No progress summary')}\n"
        else:
            answer = "[Progress Expert] No relevant progress information found."
        return answer


class AnalysisAgent(MemoryAgent):
    """Agent specialized in analysis-related questions."""

    def __init__(self, memory_file_path: str, **kwargs):
        super().__init__(memory_file_path, **kwargs)
        self.name = "analysis_agent"
        self.model = "gemini-2.0-flash"
        self.description = "Agent specialized in analysis-related questions."

    async def run(self, context: InvocationContext) -> str:
        user_message = context.session.state.get("user_message", "")
        query = user_message if user_message else ""
        # Focus on analysis reports
        results = self._memory_manager.search_similar_reports(
            query, limit=3, record_type="analysis_report"
        )
        if results:
            answer = f"[Analysis Expert]\n"
            for i, r in enumerate(results, 1):
                answer += f"{i}. {r.get('analysis_summary', 'No analysis summary')}\n"
        else:
            answer = "[Analysis Expert] No relevant analysis information found."
        return answer


class SimpleInteractionAgent(Agent):
    """
    Agent for handling simple interactions: greetings, help, and basic Q&A.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="simple_interaction_agent",
            model="gemini-2.0-flash",
            description="Handles greetings, help, and simple questions.",
            **kwargs,
        )

    async def run(self, context: InvocationContext) -> str:
        user_message = context.session.state.get("user_message", "").lower()
        if any(word in user_message for word in ["hello", "hi", "hey", "greetings"]):
            return "Hello! How can I assist you with your project today?"
        if any(
            word in user_message
            for word in ["help", "assist", "support", "how do i", "what can you do"]
        ):
            return (
                "I'm here to help! You can ask me about project progress, analysis, or any specific questions about your construction monitoring. "
                "Try asking: 'What was accomplished yesterday?' or 'Show me the latest analysis.'"
            )
        if any(
            word in user_message
            for word in ["who are you", "what are you", "your name"]
        ):
            return "I'm your project assistant, here to help monitor and analyze construction progress."
        # Add more simple Q&A as needed
        return "I'm here to help! Please ask your question about the project."


class RAGAgent(MemoryAgent):
    """
    Retrieval-Augmented Generation (RAG) agent that retrieves relevant context from Qdrant and uses Gemini LLM to answer.
    """

    _record_type: str = PrivateAttr(default=None)
    _model: str = PrivateAttr(default="gemini-2.0-pro")

    def __init__(
        self,
        memory_file_path: str,
        record_type: str = None,
        model: str = "gemini-2.0-pro",
        **kwargs,
    ):
        super().__init__(memory_file_path, **kwargs)
        self.name = "rag_agent" if not record_type else f"rag_{record_type}_agent"
        self.model = model
        self.description = f"RAG agent for answering questions using Qdrant and Gemini. Record type: {record_type or 'all'}."
        self._record_type = record_type
        self._model = model

    async def run(self, context: InvocationContext) -> str:
        user_message = context.session.state.get("user_message", "")
        query = user_message if user_message else ""
        # 1. Retrieve relevant records from Qdrant
        results = self._memory_manager.search_similar_reports(
            query, limit=3, record_type=self._record_type
        )
        # 2. Build context string
        context_str = "\n".join(
            r.get("progress_summary")
            or r.get("analysis_summary")
            or r.get("analysis_content", "")
            for r in results
        )
        if not context_str:
            return "[RAG] No relevant information found in memory."
        # 3. Compose RAG prompt
        prompt = (
            f"Context:\n{context_str}\n\n"
            f"Question: {user_message}\n\n"
            f"Answer using only the context above."
        )
        # 4. Call Gemini LLM (using ADK's LLM agent interface)
        # NOTE: This assumes self.generate is available via ADK Agent base class
        # If not, you may need to implement Gemini API call here
        if hasattr(self, "generate"):
            answer = await self.generate(prompt)
        else:
            # Fallback: just return the prompt for now
            answer = f"[RAG Prompt]\n{prompt}"
        return answer


class ProgressRAGAgent(RAGAgent):
    def __init__(self, memory_file_path: str, **kwargs):
        super().__init__(memory_file_path, record_type="progress_report", **kwargs)
        self.name = "progress_rag_agent"
        self.description = "RAG agent specialized in progress-related questions."


class AnalysisRAGAgent(RAGAgent):
    def __init__(self, memory_file_path: str, **kwargs):
        super().__init__(memory_file_path, record_type="analysis_report", **kwargs)
        self.name = "analysis_rag_agent"
        self.description = "RAG agent specialized in analysis-related questions."


# --- ADK Hierarchy Pattern: Coordinator as ParallelAgent ---
def create_coordinator_agent(memory_file_path: str):
    """
    Returns a ParallelAgent as the coordinator, with RAG sub-agents.
    """
    return ParallelAgent(
        name="coordinator_agent",
        model="gemini-2.0-flash",
        description="Coordinator agent that runs all specialized RAG agents in parallel.",
        sub_agents=[
            ProgressRAGAgent(memory_file_path),
            AnalysisRAGAgent(memory_file_path),
            RAGAgent(memory_file_path),
        ],
    )
