import os
import json
import asyncio
from typing import Any, Callable, Set, Dict, Optional
from pathlib import Path
from colorama import Fore, Style
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, ToolSet,CodeInterpreterTool,ThreadMessage
from azure.identity import DefaultAzureCredential
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI


def printFormat(message:str, color: str):
    #Print format function to print messages in different colors
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
        print(f"askADBGenieAsync Prompt: {prompt}")
        print(f"")

        theResponse = await (ask_genie(prompt, DATABRICKS_SPACE_ID, workspace_client))
    except Exception as e:
        # Handle any unexpected errors
        print(f"An error occurred: {str(e)}")
        theResponse = f"Error: {str(e)}"
    return theResponse

def askDatabaseQuestions(prompt: str) -> str:
    """
    Fetches the database information for the specified information related to:
        a. Information about racing circuits.
        b. Status codes and their descriptions.
        c. Results of sprint races.
        d. Information about racing seasons.
        e. Information about  Details of races.
        f.  Results of races.
        g. Qualifying results.
        h. Details of pit stops.
        i. Lap times for each driver.
        j.  Information about drivers.
        k.  Standings of drivers.
        L.  Information about constructors (teams).
        m. Standings of constructors.
        n.  Results of constructors in races.
        o. any other data related to formula 1.
        p.  Information about the database schema.
        q.  Information about the database tables.
    

    :param prompt  (str): the question to answwer with grounded data 
    :return: text response to the question. 
    :rtype: str
    """
    import nest_asyncio
    nest_asyncio.apply()
    answer =  asyncio.run(askADBGenieAsync(prompt))
    return answer

def InitAgent()-> tuple[str, str, AIProjectClient, ToolSet]:
    # Statically defined user functions for fast reference
    user_functions: Set[Callable[..., Any]] = {
        askDatabaseQuestions,
    }

    # Initialize agent toolset with user functions
    functions = FunctionTool(user_functions)
    theToolSet = ToolSet()
    theToolSet.add(functions)
    #Add codeinterpreter tool to for making graph and charts
    theToolSet.add(CodeInterpreterTool())

    agentInsructions = """
    Advanced asistant Agent Guidelines
    ========================================
    - Your role is to assist  users with  data inquiries with a polite, professional, and friendly tone.
    - Format all text responses in markdown format, always.
    - Before answering the user question, you must use the tool askDatabaseQuestions to get grounded data first for question realted to:
        a. Information about racing circuits.
        b. Status codes and their descriptions.
        c. Results of sprint races.
        d. Information about racing seasons.
        e. Information about  Details of races.
        f.  Results of races.
        g. Qualifying results.
        h. Details of pit stops.
        i. Lap times for each driver.
        j.  Information about drivers.
        k.  Standings of drivers.
        L.  Information about constructors (teams).
        m. Standings of constructors.
        n.  Results of constructors in races.
        o. any other data related to formula 1.
        p.  Information about the database schema.
        q.  Information about the database tables.
    
    Tools
    -----
    1. instruction to use askDatabaseQuestions
        - when you call the function askDatabaseQuestions, you must use the same prompt as the user question. you don't change the prompt.
        - When you get the response from the function askDatabaseQuestions, you must return the response to the user as is.
        - you must not change the response from the function askDatabaseQuestions.
        - Present query outputs in markdown tables with colums heads in bold unless the user specifically requests a different visualization.

    2. Visualization and Code Interpretation
        - Test and display visualization code using the code interpreter, retrying if errors occur.
        - Always use charts or graphs to illustrate trends when requested.
        - Always create visualizations as `.png` files.
        - Adapt visualizations (e.g., labels) to the user's language preferences.
        - When asked to download data, default to a `.csv` format file and use the most recent data.
        - Do not include file download links in the response


    Conduct Guidelines
    -------------------
    - Encourage Clarity: Encourage actionable and relevant questions for better assistance.
    - Out-of-Scope Queries: For non-formula-1-related or non-city-of-Boston-related quesitons or out-of-scope queries, respond:
        "I am unable to assist with that. Please contact support for further assistance."
    - Hostile Users: If users appear upset or hostile, respond:
        "I am here to help with your  data inquiries. For additional support, contact support team."
    - Unclear Queries: For unclear or unrelated queries, respond:
        "I am unable to assist with that. Please ask specific questions about Formual 1  or contact IT for further help."
    """
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
    )

    #enable_auto_function_calls
    project_client.agents.enable_auto_function_calls(toolset=theToolSet)

    # Create or get an existing agent, use your own agent ID
    agent_ID=os.environ["Agent_id"]

    try:
        myAgent = project_client.agents.get_agent(agent_ID)
        print(f"Existent agent, agent ID: {myAgent.id}")
    except Exception as e:
        myAgent = project_client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="myADBGenieAgent",
            instructions=agentInsructions,
            headers={"x-ms-enable-preview": "true"},
            toolset=theToolSet
        )
        agent_ID = myAgent.id  # Update the agent_ID with the newly created agent's ID
        print(f"Created agent, agent ID: {myAgent.id}")

    # Create a thread
    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID: {thread.id}")

    return myAgent.id, thread.id, project_client, theToolSet

myAgentID,mytheadID,myPproject_client, myToolSet = InitAgent()

def processFoundryAIAgentResponse(assitantResponse: ThreadMessage) -> tuple[str, str]:
    statement = None
    imgFullName = None  
    for myImg in assitantResponse.image_contents:
        #process image content
        imgPath=f"{Path.cwd()}\\files"
        imgNameOnly=f"{myImg.image_file.file_id}_image_file.png"
        imgFullName = f"{imgPath}\\{imgNameOnly}"
        #Save IMage content response to local disk
        myPproject_client.agents.save_file(file_id=myImg.image_file.file_id,file_name=f"{imgFullName}",target_dir=imgPath)
        #print(f"Saved image file to: {imgFullName}")
        
    for myText in assitantResponse.text_messages:
        #Process text content
        statement=myText.text.value
        #print(f"Last Message: {statement}")

    return statement, imgFullName 

def askFoundryAiAgent(string: str) -> tuple[str,str]:
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
        message = myPproject_client.agents.create_message(
            thread_id=mytheadID,
            content=string,
            role="user",
        )
        printFormat(f"Created message, message ID: {message.id}", Fore.GREEN)

        # Run the agent
        run = myPproject_client.agents.create_and_process_run(thread_id=mytheadID, agent_id=myAgentID,toolset=myToolSet)
        printFormat(f"Run finished with status: {run.status}",Fore.GREEN)

        if run.status == "failed":
            # Check if you got "Rate limit is exceeded.", then you want to get more quota
            print(f"Run failed: {run.last_error}")
            return f"Error: {run.last_error}", None

        # Get messages from the thread
        messages = myPproject_client.agents.list_messages(thread_id=mytheadID)
        
        # Get the last message from the assistant
        last_msg = messages.get_last_message_by_role("assistant")
        
        if last_msg:
            #Porcess full assitantRespose.
            textResponse, imgPathResponse = processFoundryAIAgentResponse(last_msg)   
            #printFormat(f"Last Message text: {textResponse}", Fore.GREEN)
            #printFormat(f"Last Message Img: {imgPathResponse}", Fore.GREEN)
            return textResponse, imgPathResponse
        
        #Exception case no response from the assistant
        return "No response from the assistant.", None
    except Exception as e:
        # Handle any unexpected errors
        print(f"An error occurred: {str(e)}")
        return f"Error: {str(e)}", None