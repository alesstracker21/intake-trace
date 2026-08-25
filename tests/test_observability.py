from __future__ import annotations

import asyncio

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import app.services.pipeline as pipeline_module
from app.cli import sample_requests
from app.models import AdversarialReview, IntakeProposal
from app.services.pipeline import PipelineService
from app.services.review import apply_review_policy


class FixtureExtraction:
    def __init__(self, proposal_json):
        self.proposal_json = proposal_json

    async def propose(self, intake, trace_id):
        return IntakeProposal.model_validate(self.proposal_json(1)), 1


class PassingReview:
    async def review(self, intake, proposal, validation, trace_id):
        ai_review = AdversarialReview(
            verdict="PASS",
            prompt_injection_detected=False,
            extraction_grounded=True,
            findings=[],
            recommended_action="Proceed.",
        )
        return apply_review_policy(intake.source_text, ai_review, validation), 1


def test_pipeline_emits_all_required_spans_without_source_content(proposal_json):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    original_tracer = pipeline_module.tracer
    pipeline_module.tracer = provider.get_tracer("test.pipeline")
    try:
        pipeline = PipelineService(FixtureExtraction(proposal_json), PassingReview())
        result = asyncio.run(pipeline.process(sample_requests()[0]))
    finally:
        pipeline_module.tracer = original_tracer
        provider.shutdown()

    spans = exporter.get_finished_spans()
    names = {span.name for span in spans}
    assert names == {
        "intake.processing",
        "intake.normalization",
        "intake.ai_extraction",
        "intake.evidence_validation",
        "intake.provenance_audit",
        "intake.adversarial_review",
        "intake.urgency_assessment",
        "intake.summary_creation",
        "intake.output_assembly",
    }
    serialized_attributes = str([dict(span.attributes) for span in spans]).casefold()
    assert "arun desai" not in serialized_attributes
    assert "312-555-0148" not in serialized_attributes
    assert result.trace_id == f"{spans[-1].context.trace_id:032x}"
