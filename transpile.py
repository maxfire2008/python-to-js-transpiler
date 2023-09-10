import ast
import json
import base64
import re

javascript_code = ""

with open("pycode.py", "r") as file:
    python_code = file.read()

python_ast = ast.parse(python_code)


def throw(message):
    return "\neval(" + json.dumps("throw " + json.dumps(message)) + ");\n"


def py_print(*args, **kwargs):
    js_args = []
    for arg in args:
        js_args.append(python_node_to_js(arg))

    return (
        "console.log(["
        + ", ".join(js_args)
        + "].join("
        + (python_node_to_js(kwargs["sep"]) if "sep" in kwargs else json.dumps(" "))
        + "));"
    )


def py_input(prompt):
    return "prompt(" + python_node_to_js(prompt) + ")"


def py_int(value):
    # if it's a constant, do it here, if a variable, do it in the js
    if isinstance(value, ast.Constant):
        return json.dumps(int(value.value))
    else:
        return "parseInt(" + python_node_to_js(value) + ")"


def keywords_to_dict(keywords):
    kwargs = {}
    for keyword in keywords:
        kwargs[keyword.arg] = keyword.value
    return kwargs


def python_node_to_js(node):
    if isinstance(node, ast.Assign):
        return (
            "var "
            + "python_var_"
            + base64.b16encode(node.targets[0].id.encode()).decode()
            + " /*"
            + re.sub(r"\\*/", "b*", node.targets[0].id)
            + "*/"
            + " = "
            + python_node_to_js(node.value)
            + ";"
        )
    elif isinstance(node, ast.Name):
        return (
            "python_var_"
            + base64.b16encode(node.id.encode()).decode()
            + " /* "
            + re.sub(r"\\*/", "b*", node.id)
            + " */"
        )
    elif isinstance(node, ast.Constant):
        return json.dumps(node.value)

    elif isinstance(node, ast.Expr):
        return python_node_to_js(node.value)

    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id == "print":
                return py_print(*node.args, **keywords_to_dict(node.keywords))
            elif node.func.id == "input":
                return py_input(*node.args)
            elif node.func.id == "int":
                return py_int(*node.args)
            return throw(
                "NotImplementedError: " + ast.unparse(node) + ", " + repr(type(node))
            )
    elif isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Mult):
            return python_node_to_js(node.left) + " * " + python_node_to_js(node.right)
        elif isinstance(node.op, ast.Div):
            return python_node_to_js(node.left) + " / " + python_node_to_js(node.right)
        elif isinstance(node.op, ast.Add):
            return python_node_to_js(node.left) + " + " + python_node_to_js(node.right)
        elif isinstance(node.op, ast.Sub):
            return python_node_to_js(node.left) + " - " + python_node_to_js(node.right)
    elif isinstance(node, ast.For):
        # if it uses the for i in range(x) pattern
        if (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
        ):
            # if range has 1 argument (only the stop)
            if len(node.iter.args) == 1 and len(node.iter.keywords) == 0:
                return (
                    "for (var "
                    + "python_var_"
                    + base64.b16encode(node.target.id.encode()).decode()
                    + " = 0; "
                    + "python_var_"
                    + base64.b16encode(node.target.id.encode()).decode()
                    + " < "
                    + python_node_to_js(node.iter.args[0])
                    + "; "
                    + "python_var_"
                    + base64.b16encode(node.target.id.encode()).decode()
                    + "++) {"
                    + "".join(
                        [
                            python_node_to_js(child)
                            for child in node.body
                            if not isinstance(child, ast.Pass)
                        ]
                    )
                    + "}"
                )
        else:
            return throw("NotImplementedError: " + ast.unparse(node))

    return throw("ParseError: " + ast.unparse(node) + ", " + repr(type(node)))


for node in python_ast.body:
    print(python_node_to_js(node), "|", ast.unparse(node))
    javascript_code += python_node_to_js(node)

print("\n\njavascript code:")
print(javascript_code)
