from app.agents.crew import run_triage_diagnosis


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

response = run_triage_diagnosis(event)

print("\n===== TRIAGE + DIAGNOSIS RESULT =====\n")
print(response)