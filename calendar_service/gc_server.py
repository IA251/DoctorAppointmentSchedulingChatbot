from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account


# Path to the service account JSON key file
SERVICE_ACCOUNT_FILE = "./calendar_service/gen-lang-client-0569941520-2b5f6c75848c.json"
# Google Calendar ID of the doctor
DOCTOR_CALENDAR_ID='f9ba67411e777a9ed949ddcff622968d973c9135a7cf4ae4fc1e70a3d3af7593@group.calendar.google.com'

# Initialize Flask application
app = Flask(__name__)

# Set the local timezone for appointments
TIMEZONE = ZoneInfo("Asia/Jerusalem")

# Define doctor's working hours for each weekday
WORKING_HOURS = {
    "Sunday": ("09:00", "13:00"),
    "Monday": ("09:00", "14:00"),
    "Tuesday": ("09:00", "15:00"),
    "Wednesday": ("09:00", "16:00"),
    "Thursday": ("09:00", "17:00"),
}

# Initializes and returns the Google Calendar service using a service account
def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=creds)


# Checks if the given time slot has no conflicting events in the doctor's calendar
def is_time_slot_available(service, start_time, end_time):
    events = service.events().list(
        calendarId=DOCTOR_CALENDAR_ID,
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])
    if events:
        return False
    return True

# Checks if the given time slot is within the doctor's defined working hours
def is_within_working_hours(start_time_str, end_time_str):
    try:
        start_dt = datetime.fromisoformat(start_time_str).astimezone(TIMEZONE)
        end_dt = datetime.fromisoformat(end_time_str).astimezone(TIMEZONE)
    except Exception:
        return False

    day_name = start_dt.strftime("%A")
    if day_name not in WORKING_HOURS:
        return False

    # Parse working hours for the specific day
    work_start_str, work_end_str = WORKING_HOURS[day_name]
    work_start = datetime.combine(start_dt.date(), datetime.strptime(work_start_str, "%H:%M").time(), tzinfo=TIMEZONE)
    work_end = datetime.combine(start_dt.date(), datetime.strptime(work_end_str, "%H:%M").time(), tzinfo=TIMEZONE)

    return work_start <= start_dt and end_dt <= work_end

# Ensures that the end time is after the start time
def is_end_after_start(start_time_str, end_time_str):
    try:
        start_dt = datetime.fromisoformat(start_time_str)
        end_dt = datetime.fromisoformat(end_time_str)
        return end_dt > start_dt
    except Exception:
        return False

# Ensures that both start and end times are in the future
def is_future_appointment(start_time_str, end_time_str):
    try:
        now = datetime.now(timezone.utc)
        start_dt = datetime.fromisoformat(start_time_str).astimezone(timezone.utc)
        end_dt = datetime.fromisoformat(end_time_str).astimezone(timezone.utc)
        return start_dt > now and end_dt > now
    except Exception:
        return False

# Creates a new appointment in the Google Calendar with the specified time and patient name
def create_appointment(service, start_time, end_time, name):
    event = {
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Jerusalem'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Jerusalem'},
        'summary': name,
    }
    service.events().insert(calendarId=DOCTOR_CALENDAR_ID, body=event).execute()

# Round datetime down to nearest slot of `duration` minutes.
def round_down_to_slot(dt: datetime, duration: int) -> datetime:
    minutes = (dt.minute // duration) * duration
    return dt.replace(minute=minutes, second=0, microsecond=0)

# Fetch busy event times from calendar between time_min and time_max.
def fetch_busy_times(service, calendar_id, time_min, time_max):
    events = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    return [
        (
            datetime.fromisoformat(e['start']['dateTime']).astimezone(TIMEZONE),
            datetime.fromisoformat(e['end']['dateTime']).astimezone(TIMEZONE)
        )
        for e in events
    ]





@app.route('/available_slots', methods=['GET'])
# Return available slots starting from a datetime, limited by count and duration,
# within working hours and without calendar conflicts.
def get_available_slots():
    service = get_calendar_service()

    start_str = request.args.get("start")
    duration = int(request.args.get("duration", 30))
    limit = int(request.args.get("limit", 3))

    if not start_str:
        return jsonify({"error": "Missing 'start' parameter"}), 400

    try:
        start_dt = datetime.fromisoformat(start_str).astimezone(TIMEZONE)
    except Exception as e:
        return jsonify({"error": f"Invalid 'start' datetime: {str(e)}"}), 400

    current = round_down_to_slot(start_dt, duration)
    slot_delta = timedelta(minutes=duration)
    slots = []

    time_max = current + timedelta(days=30)  
    events_result = service.events().list(
        calendarId=DOCTOR_CALENDAR_ID,
        timeMin=current.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    busy_times = [
        (datetime.fromisoformat(e['start'].get('dateTime')).astimezone(TIMEZONE),
         datetime.fromisoformat(e['end'].get('dateTime')).astimezone(TIMEZONE))
        for e in events_result.get('items', [])
    ]

    def is_free(slot_start, slot_end):
        for busy_start, busy_end in busy_times:
            if slot_start < busy_end and busy_start < slot_end:
                return False
        return True

    while len(slots) < limit:
        day_name = current.strftime("%A")
        if day_name not in WORKING_HOURS:
            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0)
            continue

        start_time_str, end_time_str = WORKING_HOURS[day_name]
        day_start = datetime.combine(current.date(), datetime.strptime(start_time_str, "%H:%M").time(), tzinfo=TIMEZONE)
        day_end = datetime.combine(current.date(), datetime.strptime(end_time_str, "%H:%M").time(), tzinfo=TIMEZONE)

        if current < day_start:
            current = day_start

        while current + slot_delta <= day_end and len(slots) < limit:
            slot_start = current
            slot_end = current + slot_delta
            if is_free(slot_start, slot_end):
                slots.append({
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat()
                })
            current += slot_delta

        current = datetime.combine(current.date() + timedelta(days=1), datetime.min.time(), tzinfo=TIMEZONE)

    return jsonify(slots)

@app.route("/book_slot", methods=["POST"])
# Book an appointment if slot is in the future, valid, available, and within working hours.

def book_slot():
    data = request.get_json()
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    name = data.get("name")

    try:
        service = get_calendar_service()
        is_available = is_time_slot_available(service, start_time, end_time)
        is_working_hours = is_within_working_hours(start_time, end_time)
        is_end_start= is_end_after_start(start_time, end_time)
        is_future = is_future_appointment(start_time, end_time)


        # Check that the times are in the future
        if not is_future:
            return jsonify({
                "status": "past",
                "message": "It is not possible to make an appointment for a time that has already passed",
                "start_time": start_time,
                "end_time": end_time
            }), 400
        elif not is_end_start:
            return jsonify({
                "status": "invalid",
                "message": "The end time must be after the start time",
                "start_time": start_time,
                "end_time": end_time
            }), 400
        elif not is_working_hours:
            return jsonify({
                "status": "unavailable",
                "message": "The time you chose is outside of business hours",
                "start_time": start_time,
                "end_time": end_time,
                "working_hours":WORKING_HOURS
            }), 400
        elif not is_available:
            return jsonify({
                "status": "busy",
                "available": False,
                "start_time": start_time,
                "end_time": end_time
            }), 409
        else:
            create_appointment(service, start_time, end_time, name)
            return jsonify({
                "status": "success",
                "message": "The appointment was successfully scheduled!",
                "start_time": start_time,
                "end_time": end_time
            }), 200

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

if __name__ == '__main__':
    app.run(port=5001, debug=True)
