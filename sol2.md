1. based on email content, extract the time window and duration of the proposed meeting using an LLM and convert this into a timestamp format
2. use the calendar retriever function to get the calendars of all the attendees for that time window
3. algorithmically search if a slot of duration is available in the time. You might need a calendar parser and searcher utility class for this.
4. if slot found, good. 
5. if slot not found, ask LLM to rank the attendee's meetings in the window and proposed meeting
6. meetings with summary(lowercase): 'weekend' and 'off hours' cannot be rescheduled and are off-limits, programmatically ignore them, don't give them to LLMs context.
7. based on these priorities again search for a slot. starting from lowest priority you can now override meetings. prefer free times