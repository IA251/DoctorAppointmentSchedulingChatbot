from flask import Flask, request, jsonify
import requests
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
from flask_cors import CORS 
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Set Gemini API key via environment variable
os.environ["GOOGLE_API_KEY"] = "AIzaSyCYjnNMugKqkhJQmt-86gEo_mqC1DyYe9s"


# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Define working hours per weekday
WORKING_HOURS = {
    "Sunday": ("09:00", "13:00"),
    "Monday": ("09:00", "14:00"),
    "Tuesday": ("09:00", "15:00"),
    "Wednesday": ("09:00", "16:00"),
    "Thursday": ("09:00", "17:00"),
}

# Instantiate language models
chat_history = []
# Extraction model
extractor_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
conversational_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.6)


# Intent detection scheme
intent_schema = [
    ResponseSchema(name="intent", description="User intent: greeting | search_slots | book_appointment | other")
]

# Create a parser and format instructions for intent detection
intent_parser = StructuredOutputParser.from_response_schemas(intent_schema)
intent_format_instructions = intent_parser.get_format_instructions()

# Function to classify user's intent
def extract_intent(user_input: str) -> str:
    prompt = f"""
    You are an intent classifier for a doctor appointment chatbot.

    User message: "{user_input}"

    Classify the user's **intent**. Choose only ONE of the following:

    - greeting → The user is just saying hello
    - search_slots → The user wants to check possible appointment times
    - book_appointment → The user is confirming a specific appointment

    Respond exactly in this JSON format:
    {intent_format_instructions}

    Chat history:
    {chat_history}
    """

    response = extractor_llm.invoke(prompt)
    result = intent_parser.parse(response.content)
    return result["intent"]

# Function to extract relevant data based on the recognized intent
def extract_data(user_input: str, intent: str):
    if intent == "search_slots":
        slot_schema = [
            ResponseSchema(name="date", description="Date in YYYY-MM-DD format (if not written 0000-00-00)"),
            ResponseSchema(name="time", description="Time in 24-hour format HH:MM:SS (if there is no target time, write 00:00:00)")
        ]
    elif intent == "book_appointment":
        slot_schema = [
            ResponseSchema(name="confirmation", description="Does the user confirm the time of the appointment? Respond with True or False."),
            ResponseSchema(name="start_datetime", description="Start date and time in full ISO format with +03:00. Example: 2025-05-14T09:00:00+03:00"),
            ResponseSchema(name="end_datetime", description="End date and time in same format. If missing, prefer defaulting to 30 minutes after start."),
            ResponseSchema(name="name", description="The user's name, if provided.")
        ]
    else:
        return {}

    parser = StructuredOutputParser.from_response_schemas(slot_schema)
    format_instructions = parser.get_format_instructions()

    prompt = f"""
    Current time: {datetime.now().isoformat(timespec='seconds')}
    User input: "{user_input}"
    User intent: {intent}

    - Always try to click a date even if a user wrote tomorrow etc.
    - If the user requested a time such as "noon", try to extract an hour within working hours and as early as possible within that time unit {WORKING_HOURS}
    Extract the following data:
    {format_instructions}
    Chat history:
    {chat_history}
    """


    response = extractor_llm.invoke(prompt)
    return parser.parse(response.content)

# Function to ask the user for any missing information politely
def ask_for_missing_info(user_input, missing_fields, intent):
    missing_fields_str = ', '.join(missing_fields)
    
    prompt = f"""
    You are a friendly and professional scheduling assistant for doctor appointments.

    Conversation so far:
    {chat_history}

    The user's latest message: "{user_input}"
    Recognized intent: {intent}
    Missing information: {missing_fields_str}

    Your task:
    - Respond politely and clearly.
    - If multiple details are missing, ask them **in one message** but clearly.
    - Use natural language (not a list of fields).
    - If the user already hinted at something in the chat history, reference it.

    Examples:
    ❌ Don't say: "Missing: date, time"
    ✅ Do say: "Great! Just to lock this in, could you please let me know what day and time work for you?"

    """.strip()

    return conversational_llm.invoke(prompt).content

# Function to get available appointment slots and generate a response message
def available_slots_and_generate_response(user_input: str, data: dict):
    date = data.get("date", datetime.now().isoformat(timespec='seconds'))
    time = data.get("time", "00:00:00")
    slots = None
    try:
        full_datetime = f"{date}T{time}%2B03:00"
        print(f"http://calendar_service:5001/available_slots?start={full_datetime}")
        url = f"http://calendar_service:5001/available_slots?start={full_datetime}"
        response = requests.get(url)
        response.raise_for_status() 
        slots = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Server request error:{e}")


    # Prompt formulation via LLM
    prompt = f"""
    The user wrote: "{user_input}"
    Extracted date: {date}
    Extracted time: {time if time else "Not provided"}

    Available slots: {slots}

    Working hours: {WORKING_HOURS}

    Instructions:
    - If the user requested today, set the time to the current time + 5 minutes.
    - If the date is in the past (e.g., yesterday including earlier today), state it as the date was or the time was.
    - If today is outside of business hours, state the days and hours of operation.
    - If the time is outside of business hours, state the hours of operation for the requested day
    - If they ask about business hours - provide them or a summary.
    - If they use a time period like "morning" - respond with the same wording.
    - If the date is correct in terms of business days and hours and the date is in the future and there are free slots - present them and encourage selection.
    - Be clear, polite, and helpful.

    Note: The goal is to help the user move forward with scheduling – don’t be too vague.

    Chat history:
    {chat_history}
    """


    response = conversational_llm.invoke(prompt)
    return response.content

# Function to attempt booking an appointment and generate a user-friendly reply
def book_appointment_and_generate_response(user_input: str, start_datetime: str, end_datetime: str, name: str) -> str:
    """
    Sends an appointment request and returns a nicely formatted response to the user.
    """
    success = False
    try:
        response = requests.post("http://calendar_service:5001/book_slot", json={
            "start_time": start_datetime,
            "end_time": end_datetime,
            "name": name
        })
        if response.status_code == 200:
            success = True
            status_message = "The appointment was successfully made! See you :)"
        else:
            status_message = f"Error in scheduling:{response.text}"
    except Exception as e:
        status_message = f"General error:{str(e)}"

    # Polite phrasing for the user (even in case of an error)
    prompt = f"""
    The user wrote: "{user_input}"
    Appointment booking attempt:
    - Start: {start_datetime}
    - End: {end_datetime}
    - Name: {name}

    Result: {status_message}

    Compose a human-like, clear, and pleasant response to the user.
    Chat history:
    {chat_history}
    """

    response = conversational_llm.invoke(prompt)
    return response.content, success

# Utility function to reset schema values if needed (currently unused)
def reset_schema_values(schemas: list[ResponseSchema]):
    for schema in schemas:
        if hasattr(schema, "value"):
            delattr(schema, "value")




# Flask route to handle incoming chat messages
@app.route("/chat", methods=["POST"])
def chat():
    success = False
    user_input = request.json.get("message", "")
    if not user_input:
        return jsonify({"reply": "I didn't receive a message."})

    # Step 1: Save user input in chat history
    chat_history.append(f"user: {user_input}")

    # Step 2: Detect intent and extract relevant data
    intent = extract_intent(user_input)
    data = extract_data(user_input, intent)
    print(intent)
    print(data)

    # Step 3: Handle each intent accordingly
    if intent == "greeting":
        reply = conversational_llm.invoke(f"""
        The user wrote: "{user_input}"
        Greet them, explain that you are a bot for scheduling appointments, and ask how you can help.
        If they try to talk about other topics, gently refocus them by explaining that this is a bot for scheduling doctor's appointments based on available times.
        Chat history:
        {chat_history}
        """).content

    elif intent == "search_slots":
        # If date is missing, ask for it
        if data.get("date") == "0000-00-00":
            reply = ask_for_missing_info(user_input, ["date"], intent)
        else:
            reply = available_slots_and_generate_response(user_input, data)

    elif intent == "book_appointment":
        start_datetime = data.get("start_datetime")
        end_datetime = data.get("end_datetime")
        name = data.get("name")

        # Detect which fields are missing
        missing_fields = []
        if not start_datetime:
            missing_fields.append("Start time")
        if not end_datetime:
            missing_fields.append("end time")
        if not name:
            missing_fields.append("name")

        if missing_fields:
            reply = ask_for_missing_info(user_input, missing_fields, intent)
        else:
            reply, success = book_appointment_and_generate_response(user_input, start_datetime, end_datetime, name)

    else:
        reply = conversational_llm.invoke(f"""
        The user wrote: "{user_input}"
        It’s unclear what they want – compose a polite question asking for clarification or guidance.
        If they try to talk about other topics, gently refocus them by explaining that this is a bot for scheduling doctor's appointments based on available times.
        Chat history:
        {chat_history}
        """).content


    # Step 4: Add assistant response to chat history and return reply
    chat_history.append(f"bot: {reply}")

    if success:
        chat_history.clear()
        reset_schema_values(intent_schema)
        intent_schema + []
        return jsonify({"reply": reply, "conversation_end": True})

    #5. Returning the response
    return jsonify({"reply": reply, "conversation_end": False})

# Define a route for resetting the chat session and schema values
@app.route("/reset", methods=["POST"])
def reset():
    # Clear the chat history
    chat_history.clear()
    # Reset all values in the intent schema to their initial state
    reset_schema_values(intent_schema)
    intent_schema + []
    # Return a JSON response indicating the reset was successful
    return jsonify({"reply": "The call has been reset. You can start over."})

if __name__ == "__main__":
    app.run(port=5000, debug=True)