# The reusable code that sends a user's request to the chosen LLM API and converts its response into a structured calendar event.
import time
from datetime import date, datetime
import json

from config import MODEL, FAST_REASONING, client
from usage import log_response
import calender_tools as cal
from calender_tools import TZ, CalendarError

# Define function tools for calendar_tools.py to allow the model to interact with the calendar
TOOLS = [
    {
        "type": "function",
        "name": "get_events",
        "description": "List calendar events in the day, week (Sunday to Saturday), or month containing the given date.",
        "parameters": {
            "type": "object",
            "properties": {
                "range": {"type": "string", "enum": ["day", "week", "month"]},
                "date": {"type": "string", "description": "Any date inside the period, as YYYY-MM-DD."},
            },
            "required": ["range", "date"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "check_availability",
        "description": "Check whether the user is free between two times.",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": "Local start time as YYYY-MM-DDTHH:MM, no timezone offset."},
                "end": {"type": "string", "description": "Local end time as YYYY-MM-DDTHH:MM, no timezone offset."},
            },
            "required": ["start", "end"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "create_event",
        "description": (
            "Create a calendar event. Only call this once the title, day, start time (with AM/PM resolved), "
            "and end time or duration are known. Refuses to double-book unless allow_conflict is true."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title."},
                "start": {"type": "string", "description": "Local start time as YYYY-MM-DDTHH:MM, no timezone offset."},
                "end": {"type": "string", "description": "Local end time as YYYY-MM-DDTHH:MM, no timezone offset."},
                "description": {"type": ["string", "null"], "description": "Optional notes, or null."},
                "allow_conflict": {
                    "type": "boolean",
                    "description": "Set true only after the user has explicitly confirmed they want an overlapping event.",
                },
            },
            "required": ["summary", "start", "end", "description", "allow_conflict"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

# Define the llm model
def llm(label, model=MODEL, **kwargs):
    """Call the Responses API, log tokens, latency, and cost under `label`, and return the response."""
    kwargs.setdefault("reasoning", FAST_REASONING)
    call = client.responses.parse if "text_format" in kwargs else client.responses.create
    t0 = time.perf_counter()
    response = call(model=model, **kwargs)
    log_response(label, response, time.perf_counter() - t0)
    return response

# Parse datetime to ensure correct syntax
def _parse(s):
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)

# Parse event details the model needs, so usage stays small
def _slim(e):
    start, end = e.get("start", {}), e.get("end", {})
    return {
        "id": e.get("id"),
        "summary": e.get("summary", "(no title)"),
        "start": start.get("dateTime", start.get("date")),  # all-day events use "date"
        "end": end.get("dateTime", end.get("date")),
        "location": e.get("location"),
    }

# Helper function model will use to run tool calls. Returns a JSON-serializable result. Errors go back to the model as data.
def run_tool(name, args):
    try:
        # get_events tool: dispatches to fetch_day / fetch_week / fetch_month in calender_tools.py
        if name == "get_events":
            d = date.fromisoformat(args["date"]) # the day, parsed for correct syntax
            fetch = {
                "day": cal.fetch_day, # calls calendar_tools.py function, fetch_day(day)
                "week": cal.fetch_week, # calls calendar_tools.py function, fetch_week(day)
                "month": lambda d: cal.fetch_month(d.year, d.month), # calls calendar_tools.py function, fetch_month(year, month)
            }[args["range"]]
            return {"events": [_slim(e) for e in fetch(d)]}
        # check_availability tool: dispatches to is_free in calendar_tools.py
        if name == "check_availability":
            return {"free": cal.is_free(_parse(args["start"]), _parse(args["end"]))} # calls calendar_tools.py function, is_free(start, end)
        # create_event tool: dispatches to add_event in calendar_tools.py
        if name == "create_event":
            event = cal.add_event( # calls calendar_tools.py function, add_event(summary, start, end, description, allow_conflict)
                args["summary"],
                _parse(args["start"]),
                _parse(args["end"]),
                description=args.get("description"),
                allow_conflict=args.get("allow_conflict", False),
            )
            return {"created": _slim(event), "link": event.get("htmlLink")}
    # Exception handlers
        return {"error": f"Unknown tool {name!r}"}
    except CalendarError as e:
        return {"error": str(e)}
    except (ValueError, KeyError) as e:
        return {"error": f"Bad arguments: {e}"}

# Helper function, builds the instruction prompt model will use
def build_instructions():
    now = datetime.now(TZ)
    return (
        "You are a calendar assistant in charge of managing calendar events. "
        f"Right now it is {now:%A, %Y-%m-%d %H:%M} in timezone {TZ}. "
        "Use your tools to read and change the calendar. Never invent events. "
        "If a request is missing a day, time, AM or PM, or is unclear which event is meant, "
        "ask one short clarifying question instead of guessing. "
        "If create_event reports an overlap, tell the user what it clashes with and ask before retrying with allow_conflict. "
        "Do not use em dashes."
    )

# Calls the model, runs any tool calls that the model makes and returns a final response.
# user_input will be either the transcribed voice request or a model prompt.
# previous_response_id is what the model returns, this allows the user to keep the converstion going with the model. 
def run_assistant(user_input, previous_response_id=None, max_steps=5):
    input_items = user_input
    for i in range(max_steps):
        # Model call
        response = llm(
            "assistant",
            instructions=build_instructions(),
            input=input_items,
            tools=TOOLS,
            previous_response_id=previous_response_id,
        )
        # Tool calls, checks for if a model has a function call within its response
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response  # response.output_text is the reply
        # Sets up the input for the model in the next iteration of the for loop
        input_items = [
            {
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(run_tool(call.name, json.loads(call.arguments))),
            }
            for call in calls
        ]
        previous_response_id = response.id
    # If model exceeds 5 step calls, raise runtime error
    raise RuntimeError("The model kept calling tools without finishing.")