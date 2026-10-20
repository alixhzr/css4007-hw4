import json
import ast
import os

CORPUS = os.path.join(os.path.dirname(__file__), "data", "corpus.jsonl")

def lookup(query: str) -> str:
    try:
        if not query or not os.path.exists(CORPUS):
            return json.dumps({"error": "Invalid query or corpus not found"})
        
        with open(CORPUS, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    text = f"{doc.get('title', '')} {doc.get('text', '')}".lower()
                    if query.lower() in text and "archived" not in text:
                        return json.dumps({"id": doc.get("id"), "title": doc.get("title"), "text": doc.get("text")})
                        
        return json.dumps({"error": f"No match found for: '{query}'"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def calculate(expression: str) -> str:
    try:
        node = ast.parse(expression, mode='eval')
        allowed = (
            ast.Expression, ast.BinOp, ast.UnaryOp, 
            ast.Add, ast.Sub, ast.Mult, ast.Div, 
            ast.USub, ast.UAdd, ast.Constant, ast.Num
        )
        
        for sub in ast.walk(node):
            if not isinstance(sub, allowed):
                return json.dumps({"error": f"Restricted operation: {type(sub).__name__}"})
                
        res = eval(compile(node, '<string>', 'eval'))
        return json.dumps({"result": res})
    except ZeroDivisionError:
        return json.dumps({"error": "Division by zero"})
    except Exception as e:
        return json.dumps({"error": str(e)})