# Import necessary libraries
import flet as ft
import logging
from genie_agent import askFoundryAiAgent


def initialize_loggin():
    # Configure logging
    logging.basicConfig(
        level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
   
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
                self.get_initials(message.user_name), color=ft.Colors.WHITE
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
            ft.Colors.AMBER,  # Updated from ft.colors to ft.Colors
            ft.Colors.BLUE,
            ft.Colors.BROWN,
            ft.Colors.CYAN,
            ft.Colors.GREEN,
            ft.Colors.INDIGO,
            ft.Colors.LIME,
            ft.Colors.ORANGE,
            ft.Colors.PINK,
            ft.Colors.PURPLE,
            ft.Colors.RED,
            ft.Colors.TEAL,
            ft.Colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]


def main(page: ft.Page):
    # Initialize the Langchain components
    logger = initialize_loggin()

    # Function to handle sending a message
    def send_message_click(e):
        send_button.disabled = True  # Disable the send button to prevent multiple clicks
        user_input = new_message.value.strip()
        # Clear the input field
        new_message.value = ""
        page.update()

        if user_input:
            # Display user's message in chat interface
            display_message(user_name, user_input,"")
            page.update()

            # Call agent_executor to get the response
            agentREsponse,agentIgmPath=askFoundryAiAgent(user_input) 

            # Display agent's response in chat interface
            display_message("Agent", agentREsponse,agentIgmPath)
            
            # Re-enable the send button
            send_button.disabled = False  
            page.update()

    def display_message(user_name, text, img):
        # Create a message object
        if user_name == "User":
            message = Message(user_name, text, "chat_message")
            chat.controls.append(ChatMessage(message))
        else:
            #Assitant Message
            message = Message(user_name, "", "chat_message")
            chat.controls.append(ChatMessage(message))
            if img:
                # Create a message object with image first
                chat.controls.append(ft.Image(src=img, width=300, height=300))
            # Text message formated with Markdown
            chat.controls.append(ft.Markdown(text,extension_set=ft.MarkdownExtensionSet.GITHUB_WEB))  # Separator line

    # Flet components setup
    user_name = "User"  # Placeholder for user name

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
        icon=ft.Icons.SEND_ROUNDED, tooltip="Send message", on_click=send_message_click
    )

    page.title = "Azure AI Agent + Genie Agent"

    # Add chat and new message entry to the page
    page.add(
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.Colors.OUTLINE),
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