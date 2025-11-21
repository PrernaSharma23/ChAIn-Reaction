from src.repository.user_repository import UserRepository
from src.service.graph_delta_service import GraphDeltaService
from src.service.impact_service import ImpactService
from src.service.prompt_service import PromptBuilder
from src.util.logger import log
from src.service.comment_notification_service import CommentNotificationService
from src.service.github_service import GitHubService
from src.service.diff_analyzer_service import DiffAnalyzerService
from src.service.llm_service import LLMService


class PullRequestService:
    def __init__(self):
        self.github = GitHubService()
        self.analyzer = DiffAnalyzerService()
        self.delta_service = GraphDeltaService()
        self.impact_service = ImpactService()
        self.notification_service = CommentNotificationService()
        self.llm = LLMService(provider="gemini")
        self.user_repository = UserRepository()

    def _fetch_pr_files(self, repo_full_name: str, pr_number: int):
        return self.github.get_pr_files(repo_full_name, pr_number)

    def _prepare_files_content(self, repo_full_name: str, files: list) -> dict:
        return self.github.build_files_content(repo_full_name, files)

    def _compute_delta(self, analysis_result: dict):
        return self.delta_service.compute_delta(
            pr_nodes=analysis_result.get("nodes", []),
            pr_edges=analysis_result.get("edges", []),
        )


    def analyze_pr(self, repo_full_name: str, pr_number: int, clone_url: str, external_only: bool = False)-> None:
        try:
            log.info(f"Analyzing PR {repo_full_name}#{pr_number} (external_only={external_only})")
            repo = self.user_repository.get_repo_by_url(clone_url)
            if not repo:
                raise Exception("Repository not found in the system. Please onboard the repo first.")
            files = self._fetch_pr_files(repo_full_name, pr_number)
            files_content = self._prepare_files_content(repo_full_name, files)
            result = self.analyzer.analyze_files(pr_number, files_content, repo)

            delta = self._compute_delta(result)
            log.info(f"Computed delta: {delta}")

            # choose impact calculation based on external_only flag
            # - external_only True: use the external-only aggregation helper that
            #   accepts the delta dict and returns only cross-repo impacted nodes
            # - otherwise, use the regular full impact graph computation
            if external_only:
                impacted_nodes = self.impact_service.get_impacted_external_graph(delta)
            else:
                impacted_nodes = self.impact_service.get_impacted_graph(delta)

            if not impacted_nodes:
                self.notification_service.post_no_impact_comment(repo_full_name, pr_number)
                return

            # build base prompt from PromptBuilder
            base_prompt = PromptBuilder.build_impact_prompt(
                pr_repo_name=repo_full_name,
                pr_number=pr_number,
                delta=delta,
                impact_nodes=impacted_nodes,
                external_only=external_only
            )

            # Prepend a short instruction that tailors the LLM behavior
            if external_only:
                header = (
                    "EXTERNAL-ONLY IMPACT REPORT\n"
                    "Focus strictly on repositories other than the PR's repo. "
                    "Do NOT enumerate intra-repo impacted nodes. For each external "
                    "repo, list repo_id, repo_name and the impacted node UIDs/paths and "
                    "a short recommended action.\n\n"
                )
            else:
                header = (
                    "FULL IMPACT REPORT\n"
                    "Provide an end-to-end impact analysis including intra-repo and cross-repo "
                    "effects. For changed components, describe the impact surface and suggested actions.\n\n"
                )

            prompt = header + base_prompt

            log.info("Calling LLM for impact analysis...")
            llm_response = self.llm.call(prompt)
            self.notification_service.post_impact_comment(repo_full_name, pr_number, llm_response)

        except Exception as e:
            log.error(f"Error analyzing PR: {e}")
            self.notification_service.post_error_comment(repo_full_name, pr_number, str(e))



