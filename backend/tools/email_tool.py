def send_email(message):
    """
    Simulates sending a notification email.
    """
    print("Sending email:", message)
    return {
        "status": "sent",
        "timestamp": "now",
        "message": message
    }
