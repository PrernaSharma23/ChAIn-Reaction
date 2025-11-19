import json
from textwrap import dedent


class PromptBuilder:

    @staticmethod
    def build_impact_prompt(pr_repo_name:str, pr_number:int, delta:dict, impact_nodes:list[dict]) -> str:
        """
        Build a model-friendly prompt for generating PR impact analysis.
        """

        added = delta.get("added", [])
        modified = delta.get("modified", {})
        deleted = delta.get("deleted", [])

        # Convert impacted nodes into a readable structure
        impacted_summary = [
            f"- [{n['kind']}] {n['name']}  (path: {n['path']})\n"
            f"  from git_repo_name: {n['repo_name']} | repo_id: {n['repo_id']}  |"
            for n in impact_nodes
        ]

        prompt = dedent(f"""
        You are an expert software architect and senior code reviewer.

        A pull request **#{pr_number}** was raised in repository **{pr_repo_name}**.
        Static impact analysis has identified changes across files, classes, 
        and methods using AST diff + Neo4j dependency graph.
        Generate a **clean, well-structured, GitHub-ready Markdown report** that will be posted as a PR comment.

        ---
        ## 1. Summary of Graph Delta
        **Added nodes**: {len(added)}
        **Modified nodes**: {len(modified)}
        **Deleted nodes**: {len(deleted)}

        ---
        ## 2. Impacted Code Elements (from dependency graph)
        These code elements are directly or transitively impacted:

        {chr(10).join(impacted_summary)}

        ---
        ## 3. Your Task
        Produce a **beautiful, concise Markdown report** with the following sections:

        ### 1. 📝 High-Level Summary
        - What the change appears to do
        - The domains or modules involved  
        - Any architectural observations

        ### B. Technical Impact
        - Which services/classes/methods are impacted and why?
        - How do the changes propagate through dependencies?
        - What upstream/downstream flows might break  
        - Any API or contract interactions  
        - A table summarizing impacted important elements like database tables, API endpoints, or external services touched.

         ### 3. ⚠ Behavioral & Risk Assessment
        - Runtime behavior implications  
        - Edge cases, regressions, potential failures  
        - Performance considerations if applicable

        ### 4. 📦 Data & Integration Impact
        - DB tables, Kafka topics, configs, external services  
        - Side-effects on request/response models  

        ### D. Recommendations
        - Testing guidelines (unit, integration, E2E)
        - Any required code reviews or validations
        - Contract/API considerations
        - Deployment risks

        ---
        ### Important: Formatting Requirements
        - Use **GitHub markdown** features:
            - `###` headings  
            - bullet lists  
            - bold text  
            - tables  
            - code blocks  
            - `<details>` collapsible sections  
        - Keep the tone professional  
        - DO NOT hallucinate classes, functions, files, or tables  
        - Do NOT hallucinate file names or classes not present in the impacted list.
        - Make inferences ONLY based on the impacted list.
        - Make the explanation readable for developers & reviewers.
        


        Begin the final formatted Markdown Impact Analysis report now.:
        """)

        return prompt
