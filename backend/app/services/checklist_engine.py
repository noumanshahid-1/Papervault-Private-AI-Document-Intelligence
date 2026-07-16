"""Generate practical checklist items and risk panels from document insights."""

from app.models.schemas import (
    ChecklistItem,
    ChecklistResult,
    DocumentInsight,
    ExtractedItem,
    RiskInsight,
    RiskPanelItem,
)


DEFAULT_CHECKLIST_STATUS = "pending"


def generate_checklist(insight: DocumentInsight) -> ChecklistResult:
    """Convert structured insights into user-actionable checklist items."""
    items: list[ChecklistItem] = []

    for date in insight.important_dates:
        _append_unique(items, _deadline_item(date))

    for requirement in insight.required_documents:
        _append_unique(items, _required_document_item(requirement))

    for action in insight.action_items:
        _append_unique(items, _action_item(action, insight.important_dates))

    for amount in insight.fees_or_amounts:
        _append_unique(items, _amount_item(amount))

    for missing in insight.missing_information:
        _append_unique(items, _missing_information_item(missing))

    for risk in insight.risks:
        _append_unique(items, _risk_checklist_item(risk))

    risk_panel = [_risk_panel_item(risk) for risk in insight.risks]
    return ChecklistResult(
        items=items,
        risks=risk_panel,
        guidance=_guidance_for_result(items, risk_panel),
    )


def _deadline_item(date: ExtractedItem) -> ChecklistItem:
    return ChecklistItem(
        title=f"Verify deadline: {date.value}",
        reason="The document appears to mention a deadline or important date. Confirm what is due and whether the date is still current.",
        priority="high",
        due_date=date.value,
        source_snippet=date.source_snippet,
        status=DEFAULT_CHECKLIST_STATUS,
    )


def _required_document_item(requirement: str) -> ChecklistItem:
    return ChecklistItem(
        title=f"Prepare required document: {requirement}",
        reason="The document appears to list this as a required supporting document.",
        priority="medium",
        due_date=None,
        source_snippet=requirement,
        status=DEFAULT_CHECKLIST_STATUS,
    )


def _action_item(action: str, dates: list[ExtractedItem]) -> ChecklistItem:
    due_date = _first_date_mentioned_in(action, dates)
    return ChecklistItem(
        title=_title_case_task(action),
        reason="The document appears to ask the reader to complete this action.",
        priority="high" if due_date else "medium",
        due_date=due_date,
        source_snippet=action,
        status=DEFAULT_CHECKLIST_STATUS,
    )


def _amount_item(amount: ExtractedItem) -> ChecklistItem:
    return ChecklistItem(
        title=f"Confirm fee or amount: {amount.value}",
        reason="The document appears to mention a fee, stipend, deposit, or payment amount. Verify whether payment is required and how it should be handled.",
        priority="medium",
        due_date=None,
        source_snippet=amount.source_snippet,
        status=DEFAULT_CHECKLIST_STATUS,
    )


def _missing_information_item(missing: str) -> ChecklistItem:
    return ChecklistItem(
        title="Resolve missing information",
        reason="The document appears to mention missing or incomplete information that may affect processing.",
        priority="high",
        due_date=None,
        source_snippet=missing,
        status=DEFAULT_CHECKLIST_STATUS,
    )


def _risk_checklist_item(risk: RiskInsight) -> ChecklistItem:
    return ChecklistItem(
        title="Review possible issue",
        reason="A possible issue was detected. Verify the source text before making a decision.",
        priority="high",
        due_date=None,
        source_snippet=risk.source_snippet,
        status=DEFAULT_CHECKLIST_STATUS,
    )


def _risk_panel_item(risk: RiskInsight) -> RiskPanelItem:
    issue = risk.issue
    if not issue.lower().startswith("possible issue"):
        issue = f"Possible issue: {issue}"
    return RiskPanelItem(
        possible_issue=issue,
        why_it_matters=risk.why_it_matters,
        suggested_verification_step=risk.suggested_verification,
        confidence_level=risk.confidence,
        source_snippet=risk.source_snippet,
    )


def _append_unique(items: list[ChecklistItem], item: ChecklistItem) -> None:
    key = (item.title.lower(), item.source_snippet or "")
    existing = {(entry.title.lower(), entry.source_snippet or "") for entry in items}
    if key not in existing:
        items.append(item)


def _first_date_mentioned_in(action: str, dates: list[ExtractedItem]) -> str | None:
    lowered = action.lower()
    for date in dates:
        if date.value.lower() in lowered:
            return date.value
    return None


def _title_case_task(action: str) -> str:
    cleaned = action.strip(" .")
    if not cleaned:
        return "Review document action"
    return cleaned[0].upper() + cleaned[1:]


def _guidance_for_result(
    items: list[ChecklistItem], risks: list[RiskPanelItem]
) -> str:
    if not items and not risks:
        return (
            "No actionable checklist items were found. Review the extracted text manually "
            "or provide a clearer document scan."
        )
    if risks:
        return (
            "Review high-priority items first and verify possible issues against the source document or responsible authority."
        )
    return "Review the checklist and verify each item against the source document."
