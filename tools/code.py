# tools/code.py
import ast
import os
from typing import Any, Dict
from ollama import chat
from config import CODER_MODEL


def analyze_codebase(file_path: str) -> Dict[str, Any]:
    """Анализ Python-файла через AST."""
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        return {"success": False, "error": f"Failed to read: {e}"}

    try:
        tree = ast.parse(code, filename=file_path)
    except SyntaxError as e:
        return {
            "success": False,
            "syntax_errors": [{
                "line": e.lineno,
                "offset": e.offset,
                "message": e.msg,
                "text": e.text.strip() if e.text else "",
            }],
        }

    definitions = []
    no_docstrings = []
    imported_names = set()
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.append({
                "type": node.__class__.__name__,
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not ast.get_docstring(node):
                no_docstrings.append({"name": node.name, "line": node.lineno})

        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)

        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)

    return {
        "success": True,
        "file_path": file_path,
        "definitions": definitions,
        "no_docstrings": no_docstrings,
        "unused_imports": list(imported_names - used_names),
        "syntax_errors": [],
    }


def generate_code_local(prompt: str, language: str = "python") -> dict:
    """Генерация кода через qwen2.5-coder."""
    try:
        system_instruction = (
            f"Ты — Senior Software Engineer. Пиши чистый, рабочий и оптимизированный "
            f"код на языке {language} с обработкой ошибок и комментариями."
        )
        response = chat(
            model=CODER_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
        )
        return {"success": True, "code": response.message.content}
    except Exception as e:
        return {"success": False, "error": f"Ошибка кодера: {e}"}