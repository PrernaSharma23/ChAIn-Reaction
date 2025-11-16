# src/extractor/java/java_ast.py
from tree_sitter import Node
from src.util.debug import dbg

class JavaAST:
    def __init__(self, repo_id:str, repo_name: str, relpath: str, src: str):
        self.repo_id = repo_id
        self.repo_name = repo_name
        self.path = relpath
        self.src = src

    def text(self, node):
        try:
            return self.src[node.start_byte:node.end_byte]
        except:
            return ""

    #TODO: set uid by repo_id
    def uid(self, kind, name):
        return f"{self.repo_name}:{self.path}:{kind}:{name}"

    def walk(self, root: Node):
        dbg("JavaAST.walk START for file", self.path)

        entities = []
        edges = []

        # file node
        file_uid = self.uid("file", self.path)
        entities.append({
            "uid": file_uid,
            "repo_id": self.repo_id
            "repo_name": self.repo_name,
            "kind": "file",
            "name": self.path,
            "language": "java",
            "path": self.path,
            "meta": "{}",
        })

        class_stack = []
        method_stack = []

        # DFS
        counter = {"visited": 0}

        def visit(node):
            counter["visited"] += 1

            dbg(f"VISIT node type={node.type} start={node.start_point} end={node.end_point}")

            t = node.type

            # -----------------------------------
            # CLASS
            # -----------------------------------
            if t == "class_declaration":
                dbg("FOUND CLASS DECLARATION")

                id_node = node.child_by_field_name("name")
                cname = self.text(id_node) if id_node else "<anon_class>"
                dbg("Class name:", cname)

                class_uid = self.uid("class", cname)

                entities.append({
                    "uid": class_uid,
                    "repo": self.repo,
                    "kind": "class",
                    "name": cname,
                    "language": "java",
                    "path": self.path,
                    "meta": "{}",
                })
                edges.append((file_uid, class_uid, "CONTAINS"))
                class_stack.append(class_uid)

                for c in node.children:
                    visit(c)

                class_stack.pop()
                return

            # -----------------------------------
            # METHOD
            # -----------------------------------
            if t == "method_declaration":
                dbg("FOUND METHOD DECLARATION")

                id_node = node.child_by_field_name("name")
                mname = self.text(id_node) if id_node else "<anon_method>"
                dbg("Method name:", mname)

                parent = class_stack[-1] if class_stack else file_uid
                method_uid = self.uid("method", mname)

                entities.append({
                    "uid": method_uid,
                    "repo_id": self.repo_id
                    "repo_name": self.repo_name,
                    "kind": "method",
                    "name": mname,
                    "language": "java",
                    "path": self.path,
                    "meta": "{}",
                })

                edges.append((parent, method_uid, "CONTAINS"))
                method_stack.append(method_uid)

                for c in node.children:
                    visit(c)

                method_stack.pop()
                return

            # -----------------------------------
            # METHOD CALL (method_invocation)
            # -----------------------------------
            if t == "method_invocation" and method_stack:
                dbg("FOUND method_invocation")

                caller = method_stack[-1]
                id_node = node.child_by_field_name("name")

                if id_node:
                    called = self.text(id_node)
                    dbg("Call target:", called)

                    target_uid = self.uid("method", called)
                    edges.append((caller, target_uid, "DEPENDS_ON"))

            # -----------------------------------
            # CONTINUE DFS
            # -----------------------------------
            for c in node.children:
                visit(c)

        visit(root)

        dbg("JavaAST.walk FINISHED. Nodes:", len(entities), "Edges:", len(edges), "Visited nodes:", counter["visited"])
        return entities, edges