# Genie Experimental Project

This project integrates Azure AI Agent and Azure Databricks Genie to create an interactive application for answering natural lenguage questions about a data. Below is a description of the key files in this project.

---

## Files Overview

### 1. `app.py`
The `app.py` file is the main application that provides a user interface for interacting with the Azure AI Agent and Genie as an agent tool. It uses the **Flet** framework to create a chat-based interface where users can send queries and receive responses from the AI agent.

#### Key Features:
- **Chat Interface**: Users can type questions into a text field and send them to the AI agent.
- **Agent Integration**: The `askFoundryAiAgent` function from `genie_agent.py` is used to process user queries and fetch responses from the Foundry AI Agent.
- **Dynamic UI**: Displays user messages and agent responses in a visually appealing format using avatars and text components.

#### How It Works:
1. Users type a question into the input field and click the send button.
2. The query is passed to the `agent_executor` function, which calls the `askFoundryAiAgent` function to get a response.
3. The response is displayed in the chat interface, and the interaction is stored in the chat history.

---

### 2. `testGenieAgent.ipynb`
The `testGenieAgent.ipynb` file is a Jupyter Notebook designed for testing and debugging the functionality implemented.

#### Key Features:
- **Function Testing**: Allows developers to test the `askFounfryAiAgent` function with various inputs to ensure it works as expected.
- **Debugging**: Provides a controlled environment to debug issues with the Agent integration.
- **Interactive Exploration**: Developers can experiment with different prompts and analyze the responses from the agent.

---



   