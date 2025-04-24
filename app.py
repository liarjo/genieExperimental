# Import necessary libraries
import flet as ft
import os
import logging
from genie_agent import askFoundryAiAgent


def initialize_loggin():
    # Configure logging
    logging.basicConfig(
        level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

   


def agent_executor(input_data, chain, logger):
   agentREsponse=askFoundryAiAgent(input_data["question"])    
   return agentREsponse


class Message:
    def __init__(self, user_name: str, text: str, message_type: str):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type


class ChatMessage(ft.Row):
    def __init__(self, message):
        super().__init__()

        # Set alignment and spacing for the row
        self.alignment = "start"
        self.spacing = 5

        # Create the avatar and text components
        avatar = ft.CircleAvatar(
            content=ft.Text(
                self.get_initials(message.user_name), color=ft.colors.WHITE
            ),
            bgcolor=self.get_avatar_color(message.user_name),
        )

        user_name_text = ft.Text(message.user_name, weight="bold")
        message_text = ft.Text(message.text, selectable=True, width=900) # message_text width determines the width of the chat row before it wraps

        # Create a column for the user name and message text
        message_column = ft.Column(
            controls=[user_name_text, message_text], tight=True, spacing=5
        )

        # Add the avatar and message column to the row
        self.controls = [avatar, message_column]

    def get_initials(self, user_name: str):
        return user_name[:1].capitalize() if user_name else "U"

    def get_avatar_color(self, user_name: str):
        # This function assigns a color based on the hash of the user name
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]


def main(page: ft.Page):
    # Initialize the Langchain components
    logger = initialize_loggin()

    # Initialize chat history
    chat_history = []

    # Function to handle sending a message
    def send_message_click(e):
        user_input = new_message.value.strip()
        # Clear the input field
        new_message.value = ""
        page.update()

        if user_input:
            # Display user's message in chat interface
            display_message(user_name, user_input)
            page.update()

            # Call agent_executor to get the response
            response = agent_executor(
                {"question": user_input, "chat_history": chat_history}, "chain", logger
            )

            # Display agent's response in chat interface
            display_message("Agent", response)

            # Append to chat history and maintain its size
            chat_history.append((user_input, response))
            if len(chat_history) > max_history:
                chat_history.pop(0)

            # Clear the input field
            #new_message.value = ""
            page.update()

    def display_message(user_name, text):
        # Create a message object
        message = Message(user_name, text, "chat_message")
        # Create a ChatMessage widget and add it to the chat ListView
        chat.controls.append(ChatMessage(message))

    # Flet components setup
    user_name = "User"  # Placeholder for user name
    max_history = 5  # Maximum size of chat history

    # Chat messages ListView
    chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    # New message entry field
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=None,  # Allow for unlimited lines
        filled=True,
        expand=True,  # Ensure the field can expand
        on_submit=send_message_click,
    )

    # Send button
    send_button = ft.IconButton(
        icon=ft.icons.SEND_ROUNDED, tooltip="Send message", on_click=send_message_click
    )
    page.title = "Azure AI Agent + Genie Agent"

    # Add chat and new message entry to the page
    page.add(
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,

        ),
        ft.Row(
            [new_message, send_button],
            alignment="end",
        ),
    )


# Run the Flet app
if __name__ == "__main__":
    ft.app(target=main)