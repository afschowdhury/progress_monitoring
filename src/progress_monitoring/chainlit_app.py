import chainlit as cl
from google.adk.agents import ParallelAgent

from progress_monitoring.chat_agents.memory_agent import (
    AnalysisRAGAgent,
    ProgressRAGAgent,
    RAGAgent,
    SimpleInteractionAgent,
)

# Path to the memory file
MEMORY_FILE = "src/progress_monitoring/my_project_memory.json"

# Instantiate specialized agents
progress_rag_agent = ProgressRAGAgent(memory_file_path=MEMORY_FILE)
analysis_rag_agent = AnalysisRAGAgent(memory_file_path=MEMORY_FILE)
general_rag_agent = RAGAgent(memory_file_path=MEMORY_FILE)
simple_interaction_agent = SimpleInteractionAgent()

# Compose multi-agent system using ADK's ParallelAgent
agent = ParallelAgent(
    name="coordinator_agent",
    sub_agents=[progress_rag_agent, analysis_rag_agent, general_rag_agent],
    model="gemini-2.0-flash",
    description="Coordinator agent that runs all specialized RAG agents in parallel.",
)


@cl.on_message
async def handle_message(message: cl.Message):
    """
    Handle incoming user messages, check for simple interactions, otherwise pass to ParallelAgent and return the response.
    """
    from uuid import uuid4

    from google.adk.agents.invocation_context import InvocationContext
    from google.adk.sessions import InMemorySessionService, Session

    session = Session(id=str(uuid4()), appName="progress-monitoring", userId="user")
    session.state["user_message"] = message.content
    session_service = InMemorySessionService()
    context = InvocationContext(
        session=session,
        session_service=session_service,
        invocation_id=str(uuid4()),
        agent=agent,
    )
    # Pre-check for simple interactions
    user_message = message.content.lower()
    if any(
        word in user_message
        for word in [
            "hello",
            "hi",
            "hey",
            "greetings",
            "help",
            "assist",
            "support",
            "how do i",
            "what can you do",
            "who are you",
            "your name",
        ]
    ):
        answer = await simple_interaction_agent.run(context)
    else:
        answer = await agent.run(context)
    await cl.Message(content=answer).send()


if __name__ == "__main__":
    cl.run()
