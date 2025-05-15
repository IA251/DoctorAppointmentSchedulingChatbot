# 🩺 Doctor Appointment Scheduling System (AI-Enhanced)

This project is a **microservices-based** appointment scheduling system for doctors, built with a modular architecture using **Flask**, **Google Calendar API**, and **Langchain with Gemini AI** for natural language understanding.

It allows users to interact conversationally with a chatbot to find and book appointments with a doctor, while integrating real-time availability from Google Calendar and enforcing business rules like working hours, time validation, and intent classification.

---

## 🧠 Features

- ✅ **Conversational AI** using **Langchain** + **Gemini (Gemini 2.0 Flash)** for:
  - Intent classification (`greeting`, `search_slots`, `book_appointment`)
  - Data extraction (date, time, confirmation, name)
  - User-friendly, dynamic response generation
- 📅 **Google Calendar integration** for:
  - Real-time availability checks
  - Booking directly into the doctor's calendar
- 🧩 **Microservices architecture**:
  - **Calendar Service**: Handles all scheduling and availability logic
  - **Chat Service**: Handles AI interactions, intent detection, and user flow
- 🐳 **Docker Compose setup**: Enables seamless orchestration of services (no need to run them individually)
- ⏰ Smart date/time handling:
  - Working hour checks
  - Future-date validation
  - Rounding to nearest appointment slot
- 🔐 Secure handling of credentials using **Google Service Accounts**
- 🌐 CORS-enabled Flask API for smooth frontend integration

---

## 🛠️ Technologies Used

| Component          | Tech Stack                                                                 |
|--------------------|----------------------------------------------------------------------------|
| Backend Services   | Python, Flask                                                              |
| AI / NLP           | [Langchain](https://www.langchain.com/), [Gemini 2.0 Flash](https://ai.google.dev) |
| Scheduling         | Google Calendar API                                                        |
| Containerization   | Docker, Docker Compose                                                     |
| Intent & Extraction| Langchain's `StructuredOutputParser` + LLM-based prompting                 |
| Time Handling      | Python `datetime`, `zoneinfo`, `timedelta`                                 |
| CORS Handling      | Flask-CORS                                                                 |

---

## 📦 Microservices Overview

This project is split into two main microservices:

### 1. **Calendar Service** (`calendar_service`)
- Exposes endpoints for:
  - `GET /available_slots`: fetches open appointment times
  - `POST /book_slot`: books a time slot
- Uses Google's Calendar API to check & write events
- Enforces working hours, availability, and time validity

### 2. **Chatbot Service** (`chat_service`)
- Exposes a single endpoint: `POST /chat`
- Uses **Langchain + Gemini AI** to:
  - Parse user messages
  - Determine intent
  - Ask for missing info
  - Respond in a conversational way
- Communicates with `calendar_service` internally to fetch or book appointments

> ⚠️ All services are **containerized** and orchestrated via Docker Compose. You **do not need to run them individually**.

---

## 🔍 Advantages of This Design

- **Separation of concerns**: Each service has a clear, independent responsibility
- **Scalable architecture**: Easy to expand or replace components (e.g., swap AI model or calendar backend)
- **Fast response time**: Thanks to Gemini’s `gemini-2.0-flash` model and preprocessed working hours logic
- **Natural user interaction**: Friendly, AI-generated messages based on full chat history
- **Error handling**: User receives helpful messages even on failure (e.g., slot busy, bad input)

---


## 🚀 Getting Started

### Clone the repo:

```bash
git clone https://github.com/IA251/DoctorAppointmentSchedulingChatbot.git
cd appointment_bot
```

### 🔐 Handling Google Credentials (Service Account)

To securely access the Google Calendar API, the system uses a Google Service Account credential file (calendar_service.json).

➡️ Please make sure to:

Obtain the calendar_service.json file from the project owner (it will be sent via email).

Place the file inside the calendar_service directory:

```
APPOINTMENT_BOT/
└── calendar_service/
    └── calendar_service.json
```

### Start the system:

```bash
docker-compose up --build
```

### 💻 Accessing the System via Browser

Once the system is up and running, you can access the user interface through your browser at:

```bash
POST http://localhost:3000
```

## 🗂️ Folder Structure

```
APPOINTMENT_BOT/
│
├── calendar_service/                # Calendar microservice
├── chatbot/                         # Chatbot backend (Python)
│   ├── chatbot.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                        # React frontend (JavaScript)
│   ├── node_modules/
│   ├── public/
│   └── src/
│       ├── App.js, DoctorChat.jsx, etc.
│   ├── Dockerfile
│   ├── package.json
│   └── package-lock.json
│
├── docker-compose.yml              # Docker Compose file to orchestrate services
├── README.md                       # Project README
└── .gitignore

```

## ✨ Example Conversation Flow

**User:** "Hi, can I book an appointment for Wednesdayat 11?"

→ **Bot:**  
“Okay, I can help with that! To book your appointment, could you please provide your name?”

**User:** "Yes, my name is Sarah."

→ **Bot:**  
“Okay Sarah, your appointment for Wednesday, May 21st at 11:00 AM is confirmed! We look forward to seeing you then”

---

Let me know if you’d like a full `docker-compose.yml` template or frontend example as well.
