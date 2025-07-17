import chainlit as cl

from progress_monitoring.chat_agents.memory_agent import CoordinatorAgent

# Path to the memory file
MEMORY_FILE = "src/progress_monitoring/my_project_memory.json"

# Initialize the coordinator agent (multi-agent system)
agent = CoordinatorAgent(memory_file_path=MEMORY_FILE)


@cl.on_message
async def handle_message(message: cl.Message):
    """
    Handle incoming user messages, pass to CoordinatorAgent, and return the response.
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
    answer = await agent.run(context)
    await cl.Message(content=answer).send()


if __name__ == "__main__":
    cl.run()
