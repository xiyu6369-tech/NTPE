from __future__ import annotations

from .models import ProviderRequestBudget, ProviderRoutingInput
from .validation import validate_budget


def calculate_request_budget(item:ProviderRoutingInput,*,planned_requests:int,planned_input_tokens:int|None=None,planned_output_tokens:int|None=None,planned_wall_clock:int|None=None)->dict:
    validate_budget(item.request_budget); b=item.request_budget
    pi=item.estimated_input_tokens*planned_requests if planned_input_tokens is None else planned_input_tokens; po=item.estimated_output_tokens*planned_requests if planned_output_tokens is None else planned_output_tokens; pw=item.timeout_budget.per_attempt_timeout_seconds*planned_requests if planned_wall_clock is None else planned_wall_clock
    usage={"chunk_requests":item.current_requests,"document_requests":item.current_document_requests,"retry_requests":item.current_retry_requests,"fallback_requests":item.current_fallback_requests,"polish_requests":item.current_polish_requests,"input_tokens":item.current_input_tokens,"output_tokens":item.current_output_tokens,"wall_clock_seconds":item.current_wall_clock_seconds}
    planned={"requests":planned_requests,"input_tokens":pi,"output_tokens":po,"wall_clock_seconds":pw}; worst={"chunk_requests":usage["chunk_requests"]+planned_requests,"document_requests":usage["document_requests"]+planned_requests,"input_tokens":usage["input_tokens"]+pi,"output_tokens":usage["output_tokens"]+po,"wall_clock_seconds":usage["wall_clock_seconds"]+pw}
    exceeded=[]
    if worst["chunk_requests"]>b.maximum_requests_per_chunk:exceeded.append("maximum_requests_per_chunk")
    if worst["document_requests"]>b.maximum_requests_per_document:exceeded.append("maximum_requests_per_document")
    if worst["input_tokens"]>b.maximum_total_input_tokens:exceeded.append("maximum_total_input_tokens")
    if worst["output_tokens"]>b.maximum_total_output_tokens:exceeded.append("maximum_total_output_tokens")
    if worst["wall_clock_seconds"]>b.maximum_wall_clock_seconds or worst["wall_clock_seconds"]>item.timeout_budget.maximum_chunk_wall_clock_seconds:exceeded.append("maximum_wall_clock_seconds")
    remaining={"chunk_requests":b.maximum_requests_per_chunk-usage["chunk_requests"],"document_requests":b.maximum_requests_per_document-usage["document_requests"],"retry_requests":b.maximum_retry_requests-usage["retry_requests"],"fallback_requests":b.maximum_fallback_requests-usage["fallback_requests"],"polish_requests":b.maximum_polish_requests-usage["polish_requests"],"input_tokens":b.maximum_total_input_tokens-usage["input_tokens"],"output_tokens":b.maximum_total_output_tokens-usage["output_tokens"],"wall_clock_seconds":b.maximum_wall_clock_seconds-usage["wall_clock_seconds"]}
    return {"valid":not exceeded,"current_usage":usage,"remaining_budget":remaining,"planned_usage":planned,"worst_case_usage":worst,"exceeded":tuple(exceeded)}
