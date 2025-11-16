from tree_sitter import Node

class PythonAST:
    def __init__(self, repo_id: str, repo_name: str, relpath: str, src: str):
        self.repo_id = repo_id
        self.repo_name = repo_name
        self.path = relpath
        self.src = src

    def text(self, node):
        return self.src[node.start_byte:node.end_byte]

    # TODO: set uid based on repo_id
    def uid(self, kind, name):
        return f"{self.repo_name}:{self.path}:{kind}:{name}"

    def walk(self, root: Node):
        entities = []
        edges = []

        file_uid = self.uid("file", self.path)
        entities.append({
            "uid": file_uid,
            "repo_id": self.repo_id,
            "repo_name": self.repo_name,
            "kind": "file",
            "name": self.path,
            "language": "python",
            "path": self.path,
            "meta": "{}",
        })

        class_stack = []
        method_stack = []

        def visit(node):
            t = node.type

            if t == "class_definition":
                id_node = node.child_by_field_name("name")
                cname = self.text(id_node) if id_node else "<anon_class>"
                class_uid = self.uid("class", cname)

                entities.append({
                    "uid": class_uid,
                    "repo_id": self.repo_id,
                    "repo_name": self.repo_name,
                    "kind": "class",
                    "name": cname,
                    "language": "python",
                    "path": self.path,
                    "meta": "{}",
                })

                edges.append((file_uid, class_uid, "CONTAINS"))
                class_stack.append(class_uid)

                for c in node.children:
                    visit(c)

                class_stack.pop()
                return

            if t == "function_definition":
                id_node = node.child_by_field_name("name")
                fname = self.text(id_node) if id_node else "<anon_function>"
                parent = class_stack[-1] if class_stack else file_uid
                method_uid = self.uid("method", fname)

                entities.append({
                    "uid": method_uid,
                    "repo_id": self.repo_id,
                    "repo_name": self.repo_name,
                    "kind": "method",
                    "name": fname,
                    "language": "python",
                    "path": self.path,
                    "meta": "{}",
                })

                edges.append((parent, method_uid, "CONTAINS"))
                method_stack.append(method_uid)

                for c in node.children:
                    visit(c)

                method_stack.pop()
                return

            if t == "call" and method_stack:
                caller = method_stack[-1]
                id_node = node.child_by_field_name("function")
                if id_node:
                    called = self.text(id_node)
                    target_uid = self.uid("method", called)
                    edges.append((caller, target_uid, "DEPENDS_ON"))

            for c in node.children:
                visit(c)

        visit(root)
        return entities, edges