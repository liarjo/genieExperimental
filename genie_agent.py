import os
import json
import asyncio
from typing import Any, Callable, Set, Dict, List, Optional
from pathlib import Path
from colorama import Fore, Style
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
import pandas as pd
import nest_asyncio



#Print format function to print messages in different colors
def printFormat(message:str, color: str):
    print(f"{color}{message}{Style.RESET_ALL}")

async def ask_genie(question: str, space_id: str,workspace_client: WorkspaceClient, conversation_id: Optional[str] = None) -> tuple[str, str]:
    """
    Asks a question to the Genie API and retrieves the response.

    This function interacts with the Genie API to start or continue a conversation, 
    execute queries, and retrieve results or messages. It uses asynchronous operations 
    to handle potentially long-running tasks.
    Parameters:
    ----------
    question : str
        The question or prompt to send to the Genie API.
    space_id : str
        The Databricks space ID where the Genie API is hosted.
    workspace_client : WorkspaceClient
        The Databricks workspace client used to interact with the Genie API.
    conversation_id : Optional[str], default=None
        The ID of an existing conversation. If not provided, a new conversation is started.

    Returns:
    -------
    tuple[str, str]
        A tuple containing:
        - The JSON response from the Genie API as a string.
        - The conversation ID used for the interaction.
    """
    try:
        genie_api = GenieAPI(workspace_client.api_client)

        loop = asyncio.get_running_loop()
        if conversation_id is None:
            initial_message = await loop.run_in_executor(None, genie_api.start_conversation_and_wait, space_id, question)
            conversation_id = initial_message.conversation_id
        else:
            initial_message = await loop.run_in_executor(None, genie_api.create_message_and_wait, space_id, conversation_id, question)

        query_result = None
        if initial_message.query_result is not None:
            query_result = await loop.run_in_executor(None, genie_api.get_message_query_result,
                space_id, initial_message.conversation_id, initial_message.id)

        message_content = await loop.run_in_executor(None, genie_api.get_message,
            space_id, initial_message.conversation_id, initial_message.id)

        
        if query_result and query_result.statement_response:
            results = await loop.run_in_executor(None, workspace_client.statement_execution.get_statement,
                query_result.statement_response.statement_id)
            
            query_description = ""
            query_query = ""
            for attachment in message_content.attachments:
                if attachment.query and attachment.query.description:
                    query_description = attachment.query.description
                    query_query=attachment.query.query
                    printFormat(f"query_description:\n {query_description}",Fore.GREEN)
                    printFormat(f"query_query:\n {query_query}",Fore.GREEN)
                    break

            return json.dumps({
                "columns": results.manifest.schema.as_dict(),
                "data": results.result.as_dict(),
                "query_description": query_description,
                "query_query": query_query,
            }), conversation_id

        if message_content.attachments:
            for attachment in message_content.attachments:
                if attachment.text and attachment.text.content:
                    return json.dumps({"message": attachment.text.content}), conversation_id

        return json.dumps({"message": message_content.content}), conversation_id
    except Exception as e:
        printFormat(f"Error in ask_genie: {str(e)}", Fore.RED)
        return json.dumps({"error": "An error occurred while processing your request."}), conversation_id
def process_query_results(answer_json: Dict) -> str:
    """
    Processes the query results from the Genie API response and formats them into a readable string.

    :param answer_json: The JSON response from the Genie API containing query results or messages.
    :return: A formatted string containing the query description, results, or message.
    """
   
    response = ""
    if "query_description" in answer_json and answer_json["query_description"]:
        response += f"## Query Description\n\n{answer_json['query_description']}\n\n"

    if "columns" in answer_json and "data" in answer_json:
        response += "## Query Results\n\n"
        columns = answer_json["columns"]
        data = answer_json["data"]
        if isinstance(columns, dict) and "columns" in columns:
            header = "| " + " | ".join(col["name"] for col in columns["columns"]) + " |"
            separator = "|" + "|".join(["---" for _ in columns["columns"]]) + "|"
            response += header + "\n" + separator + "\n"
            for row in data["data_array"]:
                formatted_row = []
                for value, col in zip(row, columns["columns"]):
                    if value is None:
                        formatted_value = "NULL"
                    elif col["type_name"] in ["DECIMAL", "DOUBLE", "FLOAT"]:
                        formatted_value = f"{float(value):,.2f}"
                    elif col["type_name"] in ["INT", "BIGINT", "LONG"]:
                        formatted_value = f"{int(value):,}"
                    else:
                        formatted_value = str(value)
                    formatted_row.append(formatted_value)
                response += "| " + " | ".join(formatted_row) + " |\n"
        else:
            response += f"Unexpected column format: {columns}\n\n"
    elif "message" in answer_json:
        response += f"{answer_json['message']}\n\n"
    else:
        response += "No data available.\n\n"
    if "query_query" in answer_json and answer_json["query_query"]:
        response += f"## Generated Code\n\n```sql\n{answer_json['query_query']}\n```\n\n"
    return response

async def askADBGenieAsync(prompt: str) -> str:
    """
    Call ADB Genie to ask a question about data
    use only for database questions!

    :param prompt  (str): the question to make to Genie assitante about data.
    :return: text response to the question. 
    :rtype: str
    """
    theResponse = ""
    try:
        # call Genie
        DATABRICKS_SPACE_ID = os.getenv("DATABRICKS_SPACE_ID")
        DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
        DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
        workspace_client = WorkspaceClient(
            host=DATABRICKS_HOST,
            token=DATABRICKS_TOKEN
        )

        print(f"")
        print(f"askDatabaseQuestions Prompt: {prompt}")
        print(f"")

        theResponse = await (ask_genie(prompt, DATABRICKS_SPACE_ID, workspace_client))
    except Exception as e:
        # Handle any unexpected errors
        print(f"An error occurred: {str(e)}")
        theResponse = f"Error: {str(e)}"
    return theResponse

def askDatabaseQuestions(prompt: str) -> str:
    """
    Fetches the database information for the specified data.
    use only for database questions!

    :param prompt  (str): the question to make to Genie assitante about data.
    :return: text response to the question. 
    :rtype: str
    """
    import nest_asyncio
    nest_asyncio.apply()
    answer, new_conversation_id =  asyncio.run(askADBGenieAsync(prompt))
    return answer

# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {
    askDatabaseQuestions,

}

# Initialize agent toolset with user functions
functions = FunctionTool(user_functions)
myToolSet = ToolSet()
myToolSet.add(functions)

agentInsructions = """
you are an agent that response user questions.
for question related to date topics listes below you must  use the function askDatabaseQuestions.
when you call the function askDatabaseQuestions, you must use the same prompt as the user question. you don't change the prompt.
When you get the response from the function askDatabaseQuestions, you must return the response to the user as is.
you must not change the response from the function askDatabaseQuestions.
the topics are:
- database schema questions
- Driver questions
"""
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
)

#enable_auto_function_calls
project_client.agents.enable_auto_function_calls(toolset=myToolSet)

# Create or get an existing agent, use your own agent ID
agent_ID="asst_tFGbBbXlVYFEGbDR2dhaLuPA"

try:
    myAgent = project_client.agents.get_agent(agent_ID)
    print(f"Existent agent, agent ID: {myAgent.id}")
except Exception as e:
    myAgent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="myADBGenieAgent",
        instructions=agentInsructions,
        headers={"x-ms-enable-preview": "true"},
        toolset=myToolSet
    )
    agent_ID = myAgent.id  # Update the agent_ID with the newly created agent's ID
    print(f"Created agent, agent ID: {myAgent.id}")

# Create a thread
thread = project_client.agents.create_thread()
print(f"Created thread, thread ID: {thread.id}")

def askFounfryAiAgent(string: str) -> str:
    """
    Sends a user query to the Foundry AI Agent and retrieves the response.

    This function interacts with the Foundry AI Agent by creating a message in a thread,
    running the agent to process the message, and retrieving the assistant's response.

    Parameters:
    ----------
    string : str
        The user query or prompt to send to the Foundry AI Agent.

    Returns:
    -------
    str
        The response from the Foundry AI Agent. If the agent fails to process the query,
        an error message is returned.
    """
    try:
        # Create a new agent message
        message = project_client.agents.create_message(
            thread_id=thread.id,
            content=string,
            role="user",
        )
        print(f"{Fore.GREEN}Created message, message ID: {message.id}")

        # Run the agent
        run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=myAgent.id,toolset=myToolSet)
        print(f"{Fore.GREEN}Run finished with status: {run.status}")

        if run.status == "failed":
            # Check if you got "Rate limit is exceeded.", then you want to get more quota
            print(f"Run failed: {run.last_error}")
            return f"Error: {run.last_error}"

        # Get messages from the thread
        messages = project_client.agents.list_messages(thread_id=thread.id)
       # print(f"Messages: {messages}")

        # Get the last message from the sender
        last_msg = messages.get_last_text_message_by_role("assistant")
        if last_msg:
            #print(f"{Fore.GREEN} Last Message: {last_msg.text.value}")
            return last_msg.text.value

        return "No response from the assistant."
    except Exception as e:
        # Handle any unexpected errors
        print(f"An error occurred: {str(e)}")
        return f"Error: {str(e)}"