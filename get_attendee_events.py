from request_to_time import extract_time_window
from get_calendar_events import retrive_calendar_events


def get_attendee_events(proposed_time, user_email):
    user = user_email
    start = proposed_time["start_time"]
    end = proposed_time["end_time"]
    return retrive_calendar_events(user, start, end)


def get_all_attendee_events(proposed_time, input_request):
    events = []
    # get sender events
    from_email = input_request["From"]
    events.append(get_attendee_events(proposed_time, from_email))
    # get all other attendees events
    for attendee in input_request["Attendees"]:
        user_email = attendee["email"]
        events.append(get_attendee_events(proposed_time, user_email))
    return events
