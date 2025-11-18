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
        self.llm = LLMService()
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

    def _post_result_comment(self, repo_full_name: str, pr_number: int, response: dict):
        self.notification_service.post_comment(repo_full_name, pr_number, response)

    def analyze_pr(self, repo_full_name: str, pr_number: int, clone_url: str) -> dict:
        try:
            log.info(f"Analyzing PR {repo_full_name}#{pr_number}")
            repo = self.user_repository.get_repo_by_url(clone_url)
            if not repo:
                raise Exception("Repository not found in the system. Please onboard the repo first.")
            files = self._fetch_pr_files(repo_full_name, pr_number)
            files_content = self._prepare_files_content(repo_full_name, files)
            result = self.analyzer.analyze_files(pr_number, files_content, repo)

            delta = self._compute_delta(result)
            log.info(f"Computed delta: {delta}")
            # TODO handles a list of impacted nodes
            impacted = self.impact_service.get_impacted_nodes(delta)

            prompt = PromptBuilder.build_impact_prompt(
                repo=repo_full_name,
                pr_number=pr_number,
                delta=delta,
                impact_nodes=impacted,
            )

            try:
                llm_response = self.llm.call(prompt)
                log.info("LLM response received")
            except Exception as e:
                log.error(f"LLM call failed: {e}")

            self._post_result_comment(repo_full_name, pr_number, llm_response)
            return result

        except Exception as e:
            log.error(f"Error analyzing PR: {e}")
            error_comment = f"## 🔗 ChAIn Reaction Analysis Error\n\n{str(e)}\n\n*Analysis failed.*"
            self.notification_service.post_comment(repo_full_name, pr_number, error_comment)
            return {"error": str(e)}


if __name__ == "__main__":
    pr_service = PullRequestService()
    repo = "PrernaSharma23/ChAIn-Reaction"
    pr_no = 1
    response = pr_service.analyze_pr(repo, pr_no)
    print(response)