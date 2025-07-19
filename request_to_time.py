"""
Meeting Request Time Extraction Module

This module provides functionality to extract meeting duration and timing information
from meeting requests using LLM-based natural language processing.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from openai import OpenAI


class MeetingTimeExtractor:
    """
    Extracts meeting time information from meeting requests using LLM.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3000/v1",
        api_key: str = "NULL",
        model_path: str = "/home/user/Models/deepseek-ai/deepseek-llm-7b-chat",
    ):
        """
        Initialize the MeetingTimeExtractor.

        Args:
            base_url: Base URL for the OpenAI-compatible API endpoint
            api_key: API key (usually "NULL" for vLLM)
            model_path: Path to the model
        """
        self.client = OpenAI(
            base_url=base_url, api_key=api_key, timeout=30, max_retries=2
        )
        self.model_path = model_path
        self.timezone_offset = "+05:30"  # IST timezone

    def extract_meeting_info(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract meeting duration and timing information from a meeting request.

        Args:
            request_data: Meeting request JSON containing Datetime, EmailContent, etc.

        Returns:
            Dict containing duration_minutes, start_time, end_time
        """
        try:
            email_content = request_data.get("EmailContent", "")
            request_datetime = request_data.get("Datetime", "")

            # Parse the request datetime
            base_datetime = self._parse_datetime(request_datetime)

            # Extract duration and timing using LLM
            extracted_info = self._extract_with_llm(email_content, request_datetime)

            # Parse the LLM response
            duration_minutes = extracted_info.get(
                "duration_minutes", 30
            )  # Default 30 minutes
            relative_time = extracted_info.get("relative_time", "")

            # Calculate start and end times
            start_time, end_time = self._calculate_meeting_times(
                base_datetime, duration_minutes, relative_time
            )

            return {
                "duration_minutes": duration_minutes,
                "start_time": start_time,
                "end_time": end_time,
                "relative_time": relative_time,
            }

        except Exception as e:
            print(f"Error extracting meeting info: {e}")
            # Return default values if extraction fails
            base_datetime = self._parse_datetime(request_data.get("Datetime", ""))
            start_time = base_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")
            end_time = (base_datetime + timedelta(minutes=30)).strftime(
                "%Y-%m-%dT%H:%M:%S%z"
            )

            return {
                "duration_minutes": 30,
                "start_time": start_time,
                "end_time": end_time,
                "relative_time": "not specified",
            }

    def _extract_with_llm(
        self, email_content: str, request_datetime: str
    ) -> Dict[str, Any]:
        """
        Use LLM to extract duration and timing information from email content.
        """
        prompt = f"""
        Extract meeting information from the following email content.
        
        Current request time: {request_datetime}
        Email content: "{email_content}"
        
        Please extract:
        1. Meeting duration in minutes (if not specified, use 30 minutes as default; if "long meeting" mentioned, use 60 minutes)
        2. Relative time mentioned (e.g., "Thursday", "next week", "Monday at 9:00 AM", "Tuesday at 11:00 AM")
        
        Return ONLY a JSON object with this exact format:
        {{
            "duration_minutes": <number>,
            "relative_time": "<time description from email>"
        }}
        
        Examples:
        - "30 minutes" → duration_minutes: 30
        - "1 hour" → duration_minutes: 60
        - "long meeting" → duration_minutes: 60
        - "Thursday" → relative_time: "Thursday"
        - "Monday at 9:00 AM" → relative_time: "Monday at 9:00 AM"
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_path,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
            )

            content = response.choices[0].message.content.strip()

            # Try to parse JSON from the response
            # Sometimes the LLM might include extra text, so we'll extract JSON
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Fallback parsing
                return self._fallback_parse(content)

        except Exception as e:
            print(f"LLM extraction error: {e}")
            return {"duration_minutes": 30, "relative_time": ""}

    def _fallback_parse(self, content: str) -> Dict[str, Any]:
        """
        Fallback parsing if JSON extraction fails.
        """
        duration_minutes = 30
        relative_time = ""

        # Look for duration indicators
        content_lower = content.lower()
        if "60" in content or "hour" in content_lower or "long" in content_lower:
            duration_minutes = 60
        elif "30" in content or "minutes" in content_lower:
            duration_minutes = 30

        # Look for time indicators
        time_patterns = [
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"(\d{1,2}:\d{2}\s*(?:am|pm)?)",
            r"(next\s+\w+)",
            r"(this\s+\w+)",
        ]

        for pattern in time_patterns:
            match = re.search(pattern, content_lower)
            if match:
                relative_time = match.group(1)
                break

        return {"duration_minutes": duration_minutes, "relative_time": relative_time}

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """
        Parse datetime string to datetime object with IST timezone.
        """
        try:
            # Parse the base datetime (assuming format: "19-07-2025T12:34:55")
            dt = datetime.strptime(datetime_str, "%d-%m-%YT%H:%M:%S")
            # Add IST timezone (UTC+05:30)
            dt = dt.replace(tzinfo=None)
            return dt
        except Exception as e:
            print(f"Error parsing datetime: {e}")
            # Return current time as fallback
            return datetime.now()

    def _calculate_meeting_times(
        self, base_datetime: datetime, duration_minutes: int, relative_time: str
    ) -> Tuple[str, str]:
        """
        Calculate start and end times based on base datetime and relative time.
        """
        try:
            # Calculate start time based on relative time
            start_dt = self._calculate_start_time(base_datetime, relative_time)

            # Calculate end time
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            # Format times with IST timezone
            start_time = start_dt.strftime("%Y-%m-%dT%H:%M:%S") + self.timezone_offset
            end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%S") + self.timezone_offset

            return start_time, end_time

        except Exception as e:
            print(f"Error calculating meeting times: {e}")
            # Return default times
            start_time = (
                base_datetime.strftime("%Y-%m-%dT%H:%M:%S") + self.timezone_offset
            )
            end_time = (base_datetime + timedelta(minutes=duration_minutes)).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ) + self.timezone_offset
            return start_time, end_time

    def _calculate_start_time(
        self, base_datetime: datetime, relative_time: str
    ) -> datetime:
        """
        Calculate actual start time from base datetime and relative time description.
        """
        relative_time_lower = relative_time.lower()

        # If no relative time specified, use next hour
        if not relative_time:
            return base_datetime.replace(minute=0, second=0) + timedelta(hours=1)

        # Handle specific time mentions like "9:00 AM", "11:00 AM"
        time_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", relative_time_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            period = time_match.group(3)

            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0

            # Find the target day
            target_date = self._find_target_date(base_datetime, relative_time_lower)
            return target_date.replace(hour=hour, minute=minute, second=0)

        # Handle day-only mentions
        target_date = self._find_target_date(base_datetime, relative_time_lower)

        # Default to 10:00 AM if no specific time mentioned
        return target_date.replace(hour=10, minute=0, second=0)

    def _find_target_date(
        self, base_datetime: datetime, relative_time: str
    ) -> datetime:
        """
        Find the target date based on relative time description.
        """
        days_of_week = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        # Check for specific day mentions
        for day_name, day_num in days_of_week.items():
            if day_name in relative_time:
                # Find next occurrence of this day
                current_day = base_datetime.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:  # If it's the same day, assume next week
                    days_ahead = 7
                return base_datetime + timedelta(days=days_ahead)

        # Handle "next week" or similar
        if "next week" in relative_time:
            return base_datetime + timedelta(days=7)
        elif "next" in relative_time:
            return base_datetime + timedelta(days=1)

        # Default to tomorrow
        return base_datetime + timedelta(days=1)


def extract_meeting_time_info(
    request_data: Dict[str, Any],
    base_url: str = "http://localhost:3000/v1",
    api_key: str = "NULL",
    model_path: str = "/home/user/Models/deepseek-ai/deepseek-llm-7b-chat",
) -> Dict[str, Any]:
    """
    Main function to extract meeting time information from a request.

    Args:
        request_data: Meeting request JSON
        base_url: Base URL for OpenAI-compatible API
        api_key: API key (usually "NULL" for vLLM)
        model_path: Path to the model

    Returns:
        Dict containing duration_minutes, start_time, end_time
    """
    extractor = MeetingTimeExtractor(
        base_url=base_url, api_key=api_key, model_path=model_path
    )
    return extractor.extract_meeting_info(request_data)


# Test functions
def test_meeting_extraction():
    """Test function for the meeting time extraction."""

    # Test cases from TestCases.ipynb
    test_cases = [
        {
            "name": "Test Case 1 - Thursday 30 minutes",
            "data": {
                "Request_id": "6118b54f-907b-4451-8d48-dd13d76033a5",
                "Datetime": "19-07-2025T12:34:55",
                "Location": "IISc Bangalore",
                "From": "userone.amd@gmail.com",
                "Attendees": [
                    {"email": "usertwo.amd@gmail.com"},
                    {"email": "userthree.amd@gmail.com"},
                ],
                "Subject": "Agentic AI Project Status Update",
                "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project.",
            },
        },
        {
            "name": "Test Case 2 - Monday 9:00 AM",
            "data": {
                "Request_id": "6118b54f-907b-4451-8d48-dd13d76033b5",
                "Datetime": "19-07-2025T12:34:55",
                "Location": "IISc Bangalore",
                "From": "userone.amd@gmail.com",
                "Attendees": [
                    {"email": "usertwo.amd@gmail.com"},
                    {"email": "userthree.amd@gmail.com"},
                ],
                "Subject": "Client Validation - Urgent",
                "EmailContent": "Hi Team. We've just received quick feedback from the client indicating that the instructions we provided aren't working on their end. Let's prioritize resolving this promptly. Let's meet Monday at 9:00 AM to discuss and resolve this issue.",
            },
        },
        {
            "name": "Test Case 3 - Tuesday 11:00 AM",
            "data": {
                "Request_id": "6118b54f-907b-4451-8d48-dd13d76033c5",
                "Datetime": "19-07-2025T12:34:55",
                "Location": "IISc Bangalore",
                "From": "userone.amd@gmail.com",
                "Attendees": [
                    {"email": "usertwo.amd@gmail.com"},
                    {"email": "userthree.amd@gmail.com"},
                ],
                "Subject": "Project Status",
                "EmailContent": "Hi Team. Let's meet on Tuesday at 11:00 A.M and discuss about our on-going Projects.",
            },
        },
        {
            "name": "Test Case 4 - Wednesday 10:00 AM",
            "data": {
                "Request_id": "6118b54f-907b-4451-8d48-dd13d76033d5",
                "Datetime": "19-07-2025T12:34:55",
                "Location": "IISc Bangalore",
                "From": "userone.amd@gmail.com",
                "Attendees": [
                    {"email": "usertwo.amd@gmail.com"},
                    {"email": "userthree.amd@gmail.com"},
                ],
                "Subject": "Client Feedback",
                "EmailContent": "Hi Team. We've received the final feedback from the client. Let's review it together and plan next steps. Let's meet on Wednesday at 10:00 A.M.",
            },
        },
    ]

    print("Testing Meeting Time Extraction...")
    print("=" * 60)

    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print("-" * 40)

        try:
            result = extract_meeting_time_info(test_case["data"])

            print(f"Email Content: {test_case['data']['EmailContent']}")
            print(f"Extracted Duration: {result['duration_minutes']} minutes")
            print(f"Start Time: {result['start_time']}")
            print(f"End Time: {result['end_time']}")
            print(f"Relative Time: {result['relative_time']}")

        except Exception as e:
            print(f"Error in test case: {e}")

    print("\n" + "=" * 60)
    print("Testing completed!")


if __name__ == "__main__":
    # Run tests
    test_meeting_extraction()
