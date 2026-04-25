class CalendarServer:
    def __init__(self):
        self.events = []

    def schedule_event(self, event, time):
        """
        Schedules an event and detects conflicts.
        """
        # Check if another event already exists at the same time
        conflict = any(e['time'] == time for e in self.events)
        
        # Add event to history
        event_data = {
            "event": event,
            "time": time
        }
        self.events.append(event_data)

        return {
            "status": "scheduled",
            "event": event,
            "time": time,
            "conflict": conflict
        }
