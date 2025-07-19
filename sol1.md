You are given an input meeting scheduling request

1. pull the calendars for the next 1 month for the attendee from the request date
2. format all of it into 1 prompt
3. format the meeting agenda, subject and other data from the request into the prompt
3. pass this prompt to an LLM call and ask it to propose a slot for the meeting
4. it should give priority to free slots
5. if no free slots are available, use smeantic understanding of the attendee's meetings to decide which can be rescheduled(eg unimportant ones)
6. fix the meeting