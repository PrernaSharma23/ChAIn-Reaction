DEBUG_AST = False

def dbg(*args):
    if DEBUG_AST:
        print("[AST-DEBUG]", *args)
