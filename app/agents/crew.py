from crewai import Crew, Process, Task

from app.agents.diagnosis_agent import build_diagnosis_agent
from app.agents.remediation_agent import build_remediation_agent
from app.agents.reporter_agent import build_reporter_agent
from app.agents.severity_agent import build_severity_agent
from app.agents.triage_agent import build_triage_agent


def build_triage_diagnosis_crew() -> Crew:
    triage_agent = build_triage_agent()
    diagnosis_agent = build_diagnosis_agent()
    remediation_agent = build_remediation_agent()
    severity_agent = build_severity_agent()
    reporter_agent = build_reporter_agent()

    triage_task = Task(
        description=(
            "Analyze this failed backend event:\n"
            "{event}\n\n"
            "Classify it into exactly one of these event types:\n"
            "- timeout_failure: a request exceeded its timeout without a clear dependency outage\n"
            "- auth_error: authentication or authorization failed\n"
            "- payload_validation_error: malformed, missing, or invalid request data\n"
            "- rate_limit: too many requests, quota exceeded, throttling, or HTTP 429\n"
            "- dependency_unavailable: an upstream/downstream service returned 5xx, was unavailable, "
            "or caused cascading failure\n"
            "- unknown: insufficient evidence to classify\n\n"
            "Classification rules:\n"
            "- Prefer dependency_unavailable when the event mentions an upstream service, 503, "
            "unavailable service, failed dependency, external dependency, or cascading failure.\n"
            "- Prefer timeout_failure only when timeout is the main symptom and no unavailable "
            "dependency is identified.\n"
            "- Prefer rate_limit only when the event explicitly mentions 429, quota, throttling, "
            "or rate limited.\n"
            "- Prefer payload_validation_error only when the event clearly mentions invalid payload, "
            "missing fields, schema validation, malformed JSON, or bad request data.\n"
            "- Prefer auth_error only when the event clearly mentions authentication, authorization, "
            "401, 403, token, permission, or credentials.\n"
            "- If the event explicitly contains P1, revenue impact, duplicate charges, many users/orders "
            "affected, customer impact, production checkout failure, or payment impact, service_tier must "
            "be critical.\n"
            "- affected_component must be the component most directly responsible for the failure, not the "
            "reporting channel.\n"
            "- Do not use discord-report as affected_component unless the Discord reporting system itself failed.\n\n"
            "Return only this exact structure, with no markdown and no extra explanation:\n"
            "event_type: one valid event type\n"
            "service_tier: critical, high, medium, or low\n"
            "affected_component: the affected service or component"
        ),
        expected_output=(
            "Exactly three lines: event_type, service_tier, and affected_component."
        ),
        agent=triage_agent,
    )

    diagnosis_task = Task(
        description=(
            "Using the triage result and the original event payload, write a detailed root cause diagnosis.\n\n"
            "Original event:\n"
            "{event}\n\n"
            "Main goal:\n"
            "- Explain what most likely went wrong and why.\n"
            "- Explain the causal chain from the first visible failure to the downstream effects.\n"
            "- Use the original event payload as evidence.\n\n"
            "Diagnosis rules:\n"
            "- Use concrete evidence from the event payload: service names, endpoints, status codes, "
            "log messages, counts, timestamps, durations, affected customers, and affected orders.\n"
            "- Distinguish between likely root cause, contributing factors, and downstream impact.\n"
            "- If the payload does not prove the exact internal cause, say that further investigation is needed.\n"
            "- Do not invent facts, dates, regions, customer names, infrastructure details, owners, ticket IDs, "
            "or metrics.\n"
            "- Do not be too short. The diagnosis should be clear enough for an engineer to understand the incident.\n\n"
            "Return the diagnosis using exactly these labels:\n"
            "Likely root cause:\n"
            "Evidence:\n"
            "Contributing factors:\n"
            "Downstream impact:\n"
            "Further investigation needed:"
        ),
        expected_output=(
            "A detailed structured diagnosis explaining likely root cause, evidence, contributing factors, "
            "downstream impact, and what still needs investigation."
        ),
        agent=diagnosis_agent,
        context=[triage_task],
    )

    remediation_task = Task(
        description=(
            "Based on the triage classification, diagnosis, and original event payload, propose a detailed "
            "actionable remediation and prevention plan.\n\n"
            "Original event:\n"
            "{event}\n\n"
            "The output must be detailed, not summarized.\n\n"
            "Main goal:\n"
            "- Explain what should be done, why it matters, and how it helps resolve or prevent the incident.\n"
            "- Include customer/business remediation, technical recovery, data repair, service recovery, "
            "prevention, and validation.\n\n"
            "Rules:\n"
            "- Include immediate customer remediation first.\n"
            "- Include immediate technical remediation.\n"
            "- Include data consistency repair steps.\n"
            "- Include service recovery steps.\n"
            "- Include long-term prevention steps.\n"
            "- Include validation checks to prove the fix worked.\n"
            "- Use concrete numbers, service names, endpoints, timestamps, and log messages from the event payload.\n"
            "- Do not claim that an action was already completed unless the event says so.\n"
            "- Do not invent owners, dates, ticket IDs, teams, cloud regions, internal dashboards, or customer names.\n"
            "- For payment/checkout incidents, include duplicate-charge reconciliation, refund verification, "
            "order status correction, idempotency review, and retry/circuit-breaker improvements when relevant.\n\n"
            "Return a detailed plan with exactly these sections:\n"
            "Immediate Customer Remediation:\n"
            "Immediate Technical Remediation:\n"
            "Data Consistency Repair:\n"
            "Service Recovery:\n"
            "Long-Term Prevention:\n"
            "Validation Checks:"
        ),
        expected_output=(
            "A detailed remediation and prevention plan explaining what to do, why it matters, "
            "and how to validate recovery."
        ),
        agent=remediation_agent,
        context=[triage_task, diagnosis_task],
    )

    severity_task = Task(
        description=(
            "Based on the original event payload, triage classification, diagnosis, and remediation output, "
            "classify the severity of this incident.\n\n"
            "Original event:\n"
            "{event}\n\n"
            "Severity rubric:\n"
            "- P1: production down, checkout/payment failure, revenue or financial impact, duplicate charges, "
            "data inconsistency, many users/orders affected, critical customer impact, or severe business impact\n"
            "- P2: degraded production, partial outage, limited customer impact, or important workflow impaired\n"
            "- P3: non-critical path failing with workaround available\n"
            "- P4: minor issue, development/staging only, cosmetic issue, or no customer impact\n\n"
            "Severity rules:\n"
            "- If the event explicitly says P1 and the payload supports critical impact, return P1.\n"
            "- If customers were charged incorrectly, payments failed, duplicate charges occurred, orders were "
            "left unconfirmed, or revenue is affected, return P1.\n"
            "- If many orders/users/customers are affected, return P1 or P2 depending on impact.\n"
            "- If the event contains concrete counts, use them as evidence.\n"
            "- Do not downgrade a payment or checkout incident with duplicate charges unless the payload clearly "
            "says it was test/staging only.\n\n"
            "Return only one value: P1, P2, P3, or P4."
        ),
        expected_output="One of: P1, P2, P3, or P4",
        agent=severity_agent,
        context=[triage_task, diagnosis_task, remediation_task],
    )

    reporter_task = Task(
        description=(
            "Generate a detailed, complete, professional Markdown incident report using all previous agent "
            "outputs AND the original event payload.\n\n"
            "Original event:\n"
            "{event}\n\n"
            "The report must contain exactly these sections:\n"
            "# Summary\n"
            "# Timeline\n"
            "# What Happened\n"
            "# Root Cause Analysis\n"
            "# Impact\n"
            "# Remediation Plan\n"
            "# Prevention Plan\n"
            "# Validation Checks\n"
            "# Follow-up Actions\n\n"
            "Main goal:\n"
            "- The report must NOT be summarized.\n"
            "- The report must be detailed and explanatory.\n"
            "- Explain what happened, why it probably happened, what evidence supports that conclusion, "
            "what systems were affected, what the business/customer impact was, and how to fix it.\n"
            "- Prefer clear operational explanation over short bullet points.\n\n"
            "Strict factual rules:\n"
            "- Do NOT use placeholders such as [Date], [Insert time], [Insert duration], [TBD], or [Unknown].\n"
            "- Do NOT invent dates, times, metrics, regions, customers, owners, ticket IDs, teams, dashboards, "
            "or internal systems that were not mentioned.\n"
            "- If a value is not provided in the event payload, write: 'Not provided in the event payload'.\n"
            "- If the original event contains timestamps, durations, counts, affected users, affected orders, "
            "service names, endpoints, or log messages, include them exactly.\n\n"
            "Timeline requirements:\n"
            "- Extract concrete timing details from the event when available.\n"
            "- Include start time, end time, duration, and detection/reporting source when available.\n"
            "- If the event says 'between 01:05 and 01:23' and '18 minutes', use those exact values.\n"
            "- If the event does not provide a real date, do not invent one.\n\n"
            "What Happened requirements:\n"
            "- Explain the incident as a sequence of events.\n"
            "- Mention the initial failure, retries, duplicate charges, database rollback, stuck orders, failed "
            "refund job, and support ticket increase when present.\n"
            "- Explain how one failure caused downstream effects.\n\n"
            "Root Cause Analysis requirements:\n"
            "- Explain the most likely root cause.\n"
            "- Include supporting evidence from logs and payload.\n"
            "- Include contributing factors separately from the root cause.\n"
            "- Explain uncertainty when the payload does not prove the exact internal cause.\n"
            "- Mention whether more investigation is needed.\n\n"
            "Impact requirements:\n"
            "- Include all concrete numbers from the payload.\n"
            "- Mention affected orders, duplicate charges, unconfirmed orders, stuck statuses, failed jobs, "
            "and support-ticket impact when present.\n"
            "- Explain customer impact and business impact.\n\n"
            "Remediation Plan requirements:\n"
            "- This section must be detailed.\n"
            "- Split it into:\n"
            "  ## Immediate Customer Remediation\n"
            "  ## Immediate Technical Remediation\n"
            "  ## Data Consistency Repair\n"
            "  ## Service Recovery\n"
            "- Explain why each action is needed.\n"
            "- Include actions such as refunding duplicate charges, confirming or cancelling affected orders, "
            "reprocessing failed refund jobs, fixing orders stuck in PROCESSING, checking payment-service health, "
            "and running database consistency checks when relevant.\n\n"
            "Prevention Plan requirements:\n"
            "- Explain how to prevent this happening again.\n"
            "- Include idempotency-key fixes, retry policy changes, circuit breaker pattern, timeout tuning, "
            "payment-service monitoring, alerting, reconciliation jobs, automated tests, and runbook updates when relevant.\n"
            "- Explain why each prevention step matters.\n\n"
            "Validation Checks requirements:\n"
            "- Explain how engineers should prove the incident is fixed.\n"
            "- Include checks for payment-service health, order status consistency, refund completion, duplicate "
            "charge reconciliation, failed job queues, and support ticket reduction when relevant.\n\n"
            "Follow-up Actions requirements:\n"
            "- Include post-incident review actions.\n"
            "- Include monitoring and alerting improvements.\n"
            "- Include test coverage or simulation improvements.\n"
            "- Include runbook or incident response improvements.\n"
            "- Include customer/support communication actions when relevant.\n"
        ),
        expected_output=(
            "A long, detailed Markdown incident report with no placeholders. The report must explain "
            "what happened, the likely cause, contributing factors, evidence, impact, detailed remediation, "
            "prevention, validation checks, and follow-up actions. It must use concrete timestamps, counts, "
            "services, endpoints, and log messages from the original event payload whenever available."
        ),
        agent=reporter_agent,
        context=[
            triage_task,
            diagnosis_task,
            remediation_task,
            severity_task,
        ],
    )

    return Crew(
        agents=[
            triage_agent,
            diagnosis_agent,
            remediation_agent,
            severity_agent,
            reporter_agent,
        ],
        tasks=[
            triage_task,
            diagnosis_task,
            remediation_task,
            severity_task,
            reporter_task,
        ],
        process=Process.sequential,
        verbose=True,
    )


def run_triage_diagnosis(event_data: dict):
    crew = build_triage_diagnosis_crew()
    return crew.kickoff(inputs={"event": event_data})
