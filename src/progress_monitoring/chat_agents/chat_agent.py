"""
Proper Google ADK Implementation
This shows the correct way to implement the RAG chatbot using ADK's execution patterns
"""

import asyncio
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

# Google ADK imports
from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.tools import FunctionTool
from google.genai import types

# Qdrant and embeddings imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class VectorDatabase:
    """Qdrant-based vector database interface for ADK"""

    def __init__(
        self,
        collection_name: str = "progress_monitoring",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
    ):
        self.collection_name = collection_name
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.qdrant_client = None
        self.embedding_model = None
        self._initialize_qdrant()
        self._initialize_embeddings()

    def _initialize_qdrant(self) -> None:
        if not QDRANT_AVAILABLE:
            print(
                "Qdrant client not available. Install with: pip install qdrant-client"
            )
            return
        try:
            self.qdrant_client = QdrantClient(
                host=self.qdrant_host, port=self.qdrant_port
            )
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                print(f"Created Qdrant collection: {self.collection_name}")
            else:
                print(f"Using existing Qdrant collection: {self.collection_name}")
        except Exception as e:
            print(f"Failed to initialize Qdrant: {e}")
            self.qdrant_client = None

    def _initialize_embeddings(self) -> None:
        if not EMBEDDINGS_AVAILABLE:
            print(
                "Sentence transformers not available. Install with: pip install sentence-transformers"
            )
            return
        try:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Initialized embedding model: all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None

    def search(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Search for relevant documents using Qdrant"""
        if not self.qdrant_client or not self.embedding_model:
            print("Qdrant or embeddings not available for search")
            return []
        try:
            query_vector = self.embedding_model.encode(query).tolist()
            search_filter = None
            if filters and "record_type" in filters:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="record_type",
                            match=models.MatchValue(value=filters["record_type"]),
                        )
                    ]
                )
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
            )
            documents = []
            for hit in search_result:
                payload = hit.payload.copy()
                documents.append(
                    {
                        "id": payload.get("id", hit.id),
                        "content": payload.get("analysis_content")
                        or payload.get("progress_summary")
                        or payload.get("analysis_summary")
                        or payload.get("progress_report")
                        or "",
                        "metadata": payload,
                        "similarity_score": hit.score,
                    }
                )
            return documents
        except Exception as e:
            print(f"Error searching Qdrant vector database: {e}")
            return []


# Global vector database instance
vector_db = VectorDatabase()


# RAG Tool Functions for ADK
async def search_progress_reports(query: str, top_k: int = 3) -> str:
    """ADK tool function to search progress reports"""
    filters = {"record_type": "progress_report"}
    documents = vector_db.search(query, top_k=top_k, filters=filters)

    if not documents:
        return "No relevant progress reports found."

    context_parts = []
    for doc in documents:
        metadata = doc["metadata"]
        context_parts.append(
            f"""
Date: {metadata.get('date', 'Unknown')}
Day: {metadata.get('day_number', 'N/A')}
Content: {doc['content'][:400]}...
Similarity: {doc['similarity_score']:.2f}
"""
        )
    return "\n---\n".join(context_parts)


async def search_analysis_reports(query: str, top_k: int = 3) -> str:
    """ADK tool function to search analysis reports"""
    filters = {"record_type": "analysis_report"}
    documents = vector_db.search(query, top_k=top_k, filters=filters)

    if not documents:
        return "No relevant analysis reports found."

    context_parts = []
    for doc in documents:
        metadata = doc["metadata"]
        context_parts.append(
            f"""
Date: {metadata.get('date', 'Unknown')}
Images Analyzed: {metadata.get('images_count', 'N/A')}
Analysis: {doc['content'][:400]}...
Similarity: {doc['similarity_score']:.2f}
"""
        )
    return "\n---\n".join(context_parts)


async def search_all_documents(query: str, top_k: int = 5) -> str:
    """ADK tool function to search all documents"""
    documents = vector_db.search(query, top_k=top_k)

    if not documents:
        return "No relevant documents found."

    context_parts = []
    for doc in documents:
        metadata = doc["metadata"]
        record_type = metadata.get("record_type", "unknown")
        context_parts.append(
            f"""
Type: {record_type}
Date: {metadata.get('date', 'Unknown')}
Content: {doc['content'][:350]}...
Similarity: {doc['similarity_score']:.2f}
"""
        )
    return "\n---\n".join(context_parts)


class ProgressReportAgent(LlmAgent):
    """ADK Agent specialized in progress report queries"""

    def __init__(self, model: str = "gemini-2.0-flash"):
        progress_search_tool = FunctionTool(func=search_progress_reports)

        super().__init__(
            name="ProgressReportAgent",
            model=model,
            instruction="""You are a progress report specialist. When you receive a query:

1. Use the search_progress_reports tool to find relevant information
2. Focus on progress-related information like milestones, achievements, and development status
3. Cite specific dates and metrics when available
4. Highlight key accomplishments and growth patterns
5. Be specific and actionable in your responses

Always search for relevant context before answering.
""",
            description="Handles queries about progress reports, milestones, achievements, and development status",
            tools=[progress_search_tool],
        )


class AnalysisAgent(LlmAgent):
    """ADK Agent specialized in analysis queries"""

    def __init__(self, model: str = "gemini-2.0-flash"):
        analysis_search_tool = FunctionTool(func=search_analysis_reports)

        super().__init__(
            name="AnalysisAgent",
            model=model,
            instruction="""You are an analysis specialist. When you receive a query:

1. Use the search_analysis_reports tool to find relevant analytical data
2. Focus on analytical insights, data patterns, and trends
3. Provide quantitative information when available
4. Highlight correlations and statistical findings
5. Make data-driven recommendations

Always search for relevant context before answering.
""",
            description="Handles analytical queries, trends, patterns, statistics, and data insights",
            tools=[analysis_search_tool],
        )


class GeneralQueryAgent(LlmAgent):
    """ADK Agent for general queries"""

    def __init__(self, model: str = "gemini-2.0-flash"):
        general_search_tool = FunctionTool(func=search_all_documents)

        super().__init__(
            name="GeneralQueryAgent",
            model=model,
            instruction="""You are a helpful assistant with access to progress reports and analysis data.

1. Use the search_all_documents tool to find relevant information
2. Use the available context to provide accurate information
3. If the context doesn't contain relevant information, say so clearly
4. Be helpful and informative
5. Suggest related topics the user might be interested in

Always search for relevant context before answering.
""",
            description="Handles general questions and provides comprehensive assistance",
            tools=[general_search_tool],
        )


class ConversationContextAgent(BaseAgent):
    """ADK Agent to manage conversation context"""

    def __init__(self, name="ConversationContextAgent", **kwargs):
        super().__init__(name=name, **kwargs)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Store the user query in session state for other agents to access"""

        # Get the user's query from the latest message
        if hasattr(ctx, "messages") and ctx.messages:
            latest_message = ctx.messages[-1]
            if hasattr(latest_message, "content"):
                ctx.session.state["user_query"] = latest_message.content

        # Initialize conversation history if not exists
        if "conversation_history" not in ctx.session.state:
            ctx.session.state["conversation_history"] = []

        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Context prepared")]),
        )


class RAGCoordinatorAgent(LlmAgent):
    """Main coordinator that routes queries to specialized agents"""

    def __init__(self, model: str = "gemini-2.0-flash"):
        # Create specialist agents
        progress_agent = ProgressReportAgent(model)
        analysis_agent = AnalysisAgent(model)
        general_agent = GeneralQueryAgent(model)

        super().__init__(
            name="RAGCoordinatorAgent",
            model=model,
            instruction="""You are the main coordinator for a RAG-based chatbot system. 
Route user queries to the most appropriate specialist agent using transfer_to_agent():

- Use transfer_to_agent(agent_name='ProgressReportAgent') for queries about:
  * Progress, milestones, achievements
  * Development status, updates
  * Growth, advancement, completion

- Use transfer_to_agent(agent_name='AnalysisAgent') for queries about:
  * Analysis, trends, patterns
  * Statistics, data insights, metrics
  * Performance comparisons

- Use transfer_to_agent(agent_name='GeneralQueryAgent') for:
  * General questions
  * When unsure about the best specialist
  * Mixed queries needing comprehensive search

Always route to one of the specialist agents rather than answering directly.
Analyze the user's query and pick the most appropriate specialist.
""",
            description="Main coordinator that intelligently routes queries to specialized RAG agents",
            sub_agents=[progress_agent, analysis_agent, general_agent],
        )


class RAGChatbotSystem(SequentialAgent):
    """Complete RAG chatbot system using ADK's SequentialAgent"""

    def __init__(self, model: str = "gemini-2.0-flash"):
        # Create the agent pipeline
        context_agent = ConversationContextAgent(name="ConversationContextAgent")
        coordinator_agent = RAGCoordinatorAgent(model)

        super().__init__(
            name="RAGChatbotSystem", sub_agents=[context_agent, coordinator_agent]
        )


# ADK Runner Implementation
class ADKChatbotRunner:
    """Proper ADK runner for the chatbot system"""

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.system = RAGChatbotSystem(model)
        self.app_name = "progress_monitoring"
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.system,
            app_name=self.app_name,
            session_service=self.session_service,
        )
        self.user_id = "user"
        self.session_id = "default"
        # Ensure session exists (await the coroutine)
        import asyncio

        try:
            asyncio.get_running_loop()
            coro = self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id,
                state={},
            )
            asyncio.create_task(coro)
        except RuntimeError:
            # No running loop, so run synchronously
            asyncio.run(
                self.session_service.create_session(
                    app_name=self.app_name,
                    user_id=self.user_id,
                    session_id=self.session_id,
                    state={},
                )
            )

    async def process_query(self, user_query: str) -> str:
        user_message = types.Content(parts=[types.Part(text=user_query)])
        events = []
        async for event in self.runner.run_async(
            user_id=self.user_id, session_id=self.session_id, new_message=user_message
        ):
            events.append(event)
        # Extract the final response
        if events:
            last_event = events[-1]
            if hasattr(last_event, "content") and last_event.content:
                if hasattr(last_event.content, "parts") and last_event.content.parts:
                    return last_event.content.parts[0].text
        return "I apologize, but I couldn't process your query properly."

    async def stream_query(self, user_query: str):
        """Stream events as they are produced for a user query."""
        user_message = types.Content(parts=[types.Part(text=user_query)])
        try:
            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=user_message,
            ):
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts") and event.content.parts:
                        yield event.content.parts[0].text
        except Exception as e:
            yield f"Error processing query: {str(e)}"


# CLI Interface
async def main():
    """Main CLI interface for the ADK chatbot"""

    # Initialize the chatbot
    print("Initializing ADK RAG Chatbot...")
    chatbot = ADKChatbotRunner()
    print("Chatbot ready! Type 'quit' to exit.\n")

    while True:
        try:
            # Get user input
            user_query = input("\nYou: ").strip()

            if user_query.lower() in ["quit", "exit", "bye"]:
                print("Goodbye!")
                break

            if not user_query:
                continue

            # Process the query
            print("\nProcessing...")
            response = await chatbot.process_query(user_query)
            print(f"\nBot: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


# Direct ADK Agent Testing
async def test_individual_agents():
    """Test individual agents directly"""
    print("Testing individual ADK agents...")
    progress_agent = ProgressReportAgent()
    print("\n=== Testing ProgressReportAgent ===")
    app_name = "progress_monitoring"
    session_service = InMemorySessionService()
    user_id = "user"
    session_id = "default"
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state={},
    )
    runner = Runner(
        agent=progress_agent, app_name=app_name, session_service=session_service
    )
    test_query = types.Content(
        parts=[types.Part(text="What progress have we made recently?")]
    )
    events = []
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=test_query
    ):
        events.append(event)
    if events:
        print(f"Response: {events[-1].content.parts[0].text}")


# if __name__ == "__main__":
#     # Set up environment
#     if not os.getenv("GOOGLE_API_KEY"):
#         print("Please set GOOGLE_API_KEY environment variable")
#         exit(1)

#     # Run the chatbot
#     asyncio.run(main())

#     # Uncomment to test individual agents
#     # asyncio.run(test_individual_agents())
