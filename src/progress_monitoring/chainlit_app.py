import chainlit as cl

from progress_monitoring.chat_agents.chat_agent import ADKChatbotRunner


@cl.on_message
async def handle_message(message: cl.Message):
    """
    Handle incoming user messages using the new ADKChatbotRunner-based RAG system, with streaming and debug logging.
    """
    import asyncio
    import logging

    chatbot = ADKChatbotRunner()
    user_query = message.content

    # Debug: Log the incoming user query
    logging.debug(f"[DEBUG] Received user query: {user_query}")
    await cl.Message(content="[DEBUG] Processing your request...").send()

    # Stream the response as it is generated
    async for chunk in chatbot.stream_query(user_query):
        if chunk and chunk.strip():
            # Debug: Log each streamed chunk
            logging.debug(f"[DEBUG] Streamed chunk: {chunk}")
            await cl.Message(content=chunk).send()

    # Debug: Indicate end of streaming
    await cl.Message(content="[DEBUG] Response complete.").send()


if __name__ == "__main__":
    cl.run()
