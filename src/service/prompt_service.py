import json
from textwrap import dedent


class PromptBuilder:

    @staticmethod
    def build_header(external_only:bool=False) -> str:
            if external_only:
               return  (
                    "EXTERNAL-ONLY IMPACT REPORT\n"
                    "Focus strictly on repositories other than the PR's repo. "
                    "Do NOT enumerate intra-repo impacted nodes. For each external "
                    "repo, list repo_id, repo_name and the impacted node UIDs/paths and "
                    "a short recommended action.\n\n"
                )
            else:
                return  (
                    "FULL IMPACT REPORT\n"
                    "Provide an end-to-end impact analysis including intra-repo and cross-repo "
                    "effects.\n\n"
                    "- Keep findings short.\n"
                    "- No architecture narration.\n\n"
                )
            

    @staticmethod
    def build_impact_prompt(pr_repo_name:str, pr_number:int, delta:dict, impact_nodes:list[dict], external_only:bool=False) -> str:
        """
        Build a model-friendly prompt for generating PR impact analysis.
        """
        header = PromptBuilder.build_header(external_only)
        updated = delta.get("modified", {})

        # Convert impacted nodes into a readable structure
        impacted_summary = [
            f"- [{n['kind']}] {n['name']}  (path: {n['path']})\n"
            f"  from git_repo_name: {n['repo_name']} | repo_id: {n['repo_id']}  |"
            for n in impact_nodes
        ]

        prompt = dedent(f"""
        You are generating a **short, concise Markdown impact table** based ONLY on the data provided.
        
        A pull request **#{pr_number}** was raised in repo **{pr_repo_name}**.  
        AST diff + Neo4j graph have identified the following changed elements.

        {header}

        ## Changed Nodes Count
        **Modified:** {len(updated)}

        ## Impacted Nodes
        {chr(10).join(impacted_summary)}

        ---
        ## 3. Your Task
        Produce a **very short, table-centric GitHub Markdown report** with:

        ### 1. ChAIn Reaction Summary (NO PARAGRAPHS)
        Columns:
        - **Area**
        - **Why Impacted**
        - **Type of Change**
        - **Risk Level**

        ### B. Code Level Impact
        Columns:
        - **Kind**
        - **Name**
        - **Repo**
        - **Path**
        - **Impact Reason**  
  

        ---
        ### HARD RULES (STRICT)
        - NO paragraphs
        - NO narration
        - NO inferred APIs, endpoints, controllers, services, DB tables
        - NO guessing missing info
        - ONLY summarize items explicitly present in the impacted list
        - Tables ONLY (no long-form explanation)
        - Keep everything compact and factual
        - No made-up architecture or flows
        - No added context beyond given node attributes

        Begin generating the FINAL Markdown tables now:
        """)

        return header + prompt
