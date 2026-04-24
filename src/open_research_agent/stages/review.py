from __future__ import annotations

from open_research_agent.core.artifacts import Artifact, StageResult
from open_research_agent.core.stage import PipelineContext, Stage
from open_research_agent.core.workspace import ResearchWorkspace


class ReviewStage(Stage):
    name = "review"

    def run(self, workspace: ResearchWorkspace, context: PipelineContext) -> StageResult:
        count = max(1, int(self.services.get("review_ensemble", 1)))
        reviews = []
        for index in range(count):
            review_context = dict(context)
            review_context["reviewer_index"] = index + 1
            reviews.append(
                self.provider.complete_json(
                    role="review_panel",
                    task="review",
                    context=review_context,
                    schema_hint={
                        "summary": "str",
                        "weaknesses": "list[str]",
                        "required_revisions": "list[str]",
                    },
                )
            )
        data = self._aggregate(reviews)
        path = workspace.write_artifact(Artifact(self.name, "review_report", data))
        md = ["# Review Report", "", f"Recommendation: {data.get('recommendation')}"]
        for weakness in data.get("weaknesses", []):
            md.append(f"- Weakness: {weakness}")
        for revision in data.get("required_revisions", []):
            md.append(f"- Required revision: {revision}")
        md_path = workspace.write_markdown("reviews", "review_report.md", "\n".join(md))
        return StageResult.ok(self.name, [path, md_path], review=data)

    @staticmethod
    def _aggregate(reviews: list[dict]) -> dict:
        if len(reviews) == 1:
            reviews[0]["ensemble_size"] = 1
            return reviews[0]
        weaknesses = []
        revisions = []
        for review in reviews:
            weaknesses.extend(review.get("weaknesses", []))
            revisions.extend(review.get("required_revisions", []))
        first = reviews[0].copy()
        first["ensemble_size"] = len(reviews)
        first["weaknesses"] = sorted(set(weaknesses))
        first["required_revisions"] = sorted(set(revisions))
        first["individual_reviews"] = reviews
        return first
