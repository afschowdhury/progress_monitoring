from google.adk.agents import LlmAgent




greeter_agent = LlmAgent(
    name="greeter_agent",
    model="gemini-2.0-flash",
    description="A simple agent that greets the user.",
    system_prompt="You are a helpful assistant that greets the user.",
)


