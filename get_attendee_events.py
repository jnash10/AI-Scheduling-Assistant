from request_to_time import extract_time_window
from get_calendar_events import retrive_calendar_events


def get_attendee_events(proposed_time, user_email):
    """get the attendee's calendar events for:
    1. the day of the propose start_time
    2. the next day of the proposed end_time"""
    user = user_email
    start_day = proposed_time["start_time"].split("T")[0]
    end_day = proposed_time["end_time"].split("T")[0]
    end_day_plus_one = proposed_time["end_time"].split("T")[0]
    end_day_plus_one = end_day_plus_one.split("-")
    end_day_plus_one[2] = str(int(end_day_plus_one[2]) + 1)
    end_day_plus_one = "-".join(end_day_plus_one)

    start_day_time_stamp = f"{start_day}T00:00:00+05:30"
    end_day_time_stamp = f"{end_day}T23:59:59+05:30"
    end_day_plus_one_time_stamp = f"{end_day_plus_one}T23:59:59+05:30"

    events = retrive_calendar_events(
        user, start_day_time_stamp, end_day_plus_one_time_stamp
    )

    return events


def get_all_attendee_events(proposed_time, input_request):
    """Get all attendees' calendar events for the proposed time window's day plus the next day."""
    events = {}
    # get sender events
    from_email = input_request["From"]
    events[from_email] = get_attendee_events(proposed_time, from_email)
    # get all other attendees events
    for attendee in input_request["Attendees"]:
        user_email = attendee["email"]
        events[user_email] = get_attendee_events(proposed_time, user_email)
    return events
