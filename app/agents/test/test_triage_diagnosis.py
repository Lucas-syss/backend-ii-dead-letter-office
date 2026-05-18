from app.services.crew_service import run_crew


event = {
    "source": "webhook",
    "service": "payment-service",
    "error_code": 503,
    "error_message": "Upstream timeout after 30s",
    "payload": {
        "endpoint": "/charge",
        "method": "POST",
    },
    "metadata": {
        "environment": "production",
        "region": "eu-west-1",
    },
}

response = run_crew(event)

print("\n===== CREW REPORT RESULT =====\n")
print("Success:", response["success"])
print("Report path:", response["report_path"])

print("\n===== REPORT CONTENT =====\n")
print(response["report"])