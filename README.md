# Genie Experimental Project

This project integrates Azure AI and Azure Databricks Genie to create an interactive application for querying and managing data. Below is a description of the key files in this project.

---

## Files Overview

### 1. `app.py`
The `app.py` file is the main application that provides a user interface for interacting with the Genie Agent. It uses the **Flet** framework to create a chat-based interface where users can send queries and receive responses from the AI agent.

#### Key Features:
- **Chat Interface**: Users can type questions into a text field and send them to the AI agent.
- **Agent Integration**: The `askFoundryAiAgent` function from `genie_agent.py` is used to process user queries and fetch responses from the Foundry AI Agent.
- **Chat History**: Maintains a history of the last 5 interactions between the user and the agent.
- **Dynamic UI**: Displays user messages and agent responses in a visually appealing format using avatars and text components.

#### How It Works:
1. Users type a query into the input field and click the send button.
2. The query is passed to the `agent_executor` function, which calls the `askFoundryAiAgent` function to get a response.
3. The response is displayed in the chat interface, and the interaction is stored in the chat history.

---

### 2. `testGenieAgent.ipynb`
The `testGenieAgent.ipynb` file is a Jupyter Notebook designed for testing and debugging the functionality of the Genie Agent.

#### Key Features:
- **Function Testing**: Allows developers to test the `askFounfryAiAgent` function with various inputs to ensure it works as expected.
- **Debugging**: Provides a controlled environment to debug issues with the Genie Agent integration.
- **Interactive Exploration**: Developers can experiment with different prompts and analyze the responses from the agent.

#### How It Works:
1. The notebook imports the `askFounfryAiAgent` function from `genie_agent.py`.
2. Developers can run test cases by providing sample queries and observing the agent's responses.
3. Any issues or unexpected behavior can be logged and analyzed for further debugging.

---

## Prerequisites
- Python 3.8 or higher
- Required Python libraries: `flet`, `azure-ai-projects`, `databricks-sdk`, `colorama`, `pandas`, `nest_asyncio`
- Properly configured environment variables for Azure and Azure Databricks integration.

---

## How to Run

### Running the Application (`app.py`):
1. Install the required dependencies:
   ```bash
   pip install flet azure-ai-projects databricks-sdk colorama pandas nest_asyncio
   