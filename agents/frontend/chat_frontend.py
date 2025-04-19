import streamlit as st
import requests
import uuid
import json
from io import BytesIO # Needed for file handling

# --- Configuration ---
# IMPORTANT: Make sure your n8n webhook URL can handle multipart/form-data
WEBHOOK_URL = "http://localhost:5678/webhook/invoke_agent"
CHAT_TITLE = "Chat with n8n LLM Agent (with File Upload)"
AVATAR_USER = "👤"
AVATAR_ASSISTANT = "🤖"

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- Helper Function ---
def send_to_webhook(session_id, user_input, uploaded_file_object=None):
    """
    Sends user input and optionally a file to the n8n webhook.
    Uses multipart/form-data if a file is present, otherwise sends JSON.
    (Revised: Always uses multipart/form-data for consistency on the n8n side)
    """
    data_payload = {
        "sessionld": session_id,
        "chatinput": user_input
    }
    files_payload = {}
    headers = {} # Let requests determine Content-Type for multipart

    if uploaded_file_object is not None:
        # Prepare file for multipart upload
        file_bytes = uploaded_file_object.getvalue()
        files_payload = {
            'file': (uploaded_file_object.name, file_bytes, uploaded_file_object.type)
            # 'file' is the field name n8n expects for binary data
        }
        st.sidebar.write(f"DEBUG: Preparing file '{uploaded_file_object.name}' for upload.")

    try:
        # Always send as multipart/form-data now
        # requests handles the Content-Type header automatically
        response = requests.post(
            WEBHOOK_URL,
            data=data_payload,
            files=files_payload if files_payload else None, # Pass files dict only if it's not empty
            headers=headers, # Pass empty headers dict
            timeout=180 # Increased timeout for potential file upload
        )
        response.raise_for_status() # Check for HTTP errors

        response_data = response.json()
        # DEBUG: Uncomment the line below to see the response
        # st.sidebar.write(f"DEBUG: Received response: {json.dumps(response_data)}")

        if "output" in response_data:
            return response_data["output"]
        else:
            st.error(f"Error: Unexpected response format. 'output' key missing. Response: {response_data}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to webhook: {e}")
        # If it's a 4xx/5xx error, response might have details
        if e.response is not None:
            st.error(f"Webhook response content: {e.response.text}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON response from webhook. Response text: {response.text}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

# --- Streamlit App Layout ---

st.set_page_config(page_title=CHAT_TITLE, layout="centered")
st.title(CHAT_TITLE)

# --- Sidebar ---
with st.sidebar:
    st.header("Controls & Info")
    st.write(f"**Session ID:**")
    st.caption(f"`{st.session_state.session_id}`")
    st.divider()


    # --- End File Uploader ---

    st.divider()

    if st.button("Clear Chat History"):
        st.session_state.messages = []
        # Optionally clear the file uploader too if desired upon clearing history
        # uploaded_file = None # This won't directly clear the widget state from here easily
        # A rerun is usually needed. The rerun below handles the message clearing display.
        st.rerun()

    st.divider()
    st.markdown("Ensure your n8n workflow at the configured URL can accept `multipart/form-data` with fields `sessionld`, `chatinput`, and optionally `file`.")


# --- Main Chat Interface ---

# Display chat messages from history
for message in st.session_state.messages:
    avatar = AVATAR_USER if message["role"] == "user" else AVATAR_ASSISTANT
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"]) # Display text content
        if "file_info" in message: # Check if file info is stored with the message
             st.caption(f"📎 Sent with file: {message['file_info']}")

# Replace sidebar uploader + chat_input with in-line uploader next to send button
cols = st.columns([4, 1], gap="small")
with cols[0]:
    prompt = st.chat_input("Ask something or describe what to do…", key="chat_input")
with cols[1]:
    uploaded_file = st.file_uploader(
        "", key="file_uploader", label_visibility="collapsed"
    )


# React to user input
if prompt:
    # --- Prepare message data ---
    user_message = {"role": "user", "content": prompt}
    current_file = uploaded_file # Get the file from the widget state at the time of submission

    # Add file info to the message if a file is attached for display purposes
    if current_file:
        file_info_text = f"{current_file.name} ({current_file.size} bytes)"
        user_message["file_info"] = file_info_text # Store file info
        prompt_display = f"{prompt}\n\n*(Sending with file: {file_info_text})*"
    else:
        prompt_display = prompt

    # --- Add and display user message ---
    st.session_state.messages.append(user_message)
    with st.chat_message("user", avatar=AVATAR_USER):
        st.markdown(prompt_display) # Display prompt potentially annotated with file info

    # --- Get assistant response ---
    with st.chat_message("assistant", avatar=AVATAR_ASSISTANT):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        # Send user input (and potentially file) to webhook
        assistant_response = send_to_webhook(
            st.session_state.session_id,
            prompt, # Send the original prompt text
            current_file # Pass the file object if it exists
        )

        if assistant_response:
            message_placeholder.markdown(assistant_response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})

            # --- IMPORTANT: Clear the file uploader state after successful processing? ---
            # Decide if you want the file to be cleared automatically after sending.
            # Streamlit widget state management can be tricky. Often, letting the user
            # manage the uploader (clearing it manually via the 'x') is simplest.
            # If you *need* programmatic clearing, it often requires more complex state handling.
            # For now, we are *not* clearing it programmatically. The same file will be sent
            # with subsequent messages unless the user clears it or uploads a new one.
            # If automatic clearing is essential, you might need techniques involving
            # callback functions on the chat_input or button, and managing the uploader's
            # state more explicitly via st.session_state and assigning None to its key
            # followed by st.rerun().

        else:
            message_placeholder.markdown("Sorry, I encountered an error trying to get a response.")

# --- To Run the App ---
# 1. Make sure your n8n workflow is updated for multipart/form-data.
# 2. Save this code as app.py
# 3. Run: streamlit run app.py