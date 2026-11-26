# Connect all the components. Accept the user's speech, obtain a transcription, call the LLM, validate the proposed event, request confirmation, execute the calendar tool, and speak the result.
from flask import Flask, jsonify, request, send_from_directory

import calender_tools as cal
from llm_parser import run_assistant, _slim
from speech import transcribe, voice_call

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory("templates", "index.html")

# Displays a text box that will be used to call the model
@app.post("/api/chat")
def chat():
    data = request.get_json(force=True)
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify(error="Empty message"), 400
    try:
        response = run_assistant(text, previous_response_id=data.get("previous_response_id"))
    except Exception as e:
        return jsonify(error=f"{type(e).__name__}: {e}"), 500
    return jsonify(reply=response.output_text, response_id=response.id)

# Displays a microphone allowing the user to record what they say, will be inputed into the text box
@app.post("/api/transcribe")
def transcribe_audio():
    f = request.files.get("audio")
    if f is None:
        return jsonify(error="No audio received"), 400
    text = voice_call(
        "Speech-to-text", transcribe, f.read(),
        filename=f.filename or "speech.webm", content_type=f.mimetype or "audio/webm",
    )
    if not text:
        return jsonify(error="Transcription failed"), 502
    return jsonify(text=text)

# Displays the users schedule in a monthly calendar view
@app.get("/api/events")
def events():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    # Returns 400 error if the month is not between 1 and 12
    if month is not None and not 1 <= month <= 12:
        return jsonify(error="month must be between 1 and 12"), 400
    try:
        items = cal.fetch_month(year, month)
    except cal.CalendarError as e:
        return jsonify(error=str(e)), 502
    return jsonify(events=[_slim(e) for e in items])

if __name__ == '__main__':
    app.run(port=3000, debug=True)