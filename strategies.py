import os
import json
import time
from pathlib import Path
from openai import OpenAI
from tools import lookup, calculate


env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip("'\"")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL_NAME = "gpt-5.6-luna"

TOOLS_DEF = [
    {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": "Searches corpus for district profiles, water prices, and notes.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Safely evaluates math expressions using AST.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            }
        }
    }
]

def run_s1(question, documents_text):
    """S1: Прямой промпт со всеми документами."""
    prompt = f"Documents:\n{documents_text}\n\nQuestion: {question}\n\nEnd your reply with: ANSWER: <name or yes/no> | <number>"
    start = time.time()
    res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        reasoning_effort="none"
    )
    duration = time.time() - start
    return res.choices[0].message.content, res.usage, duration

def run_s2(question, documents_text, k=5):
    """S2: Think and vote (k=5 выборок)."""
    answers = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    start = time.time()
    
    for _ in range(k):
        prompt = f"Documents:\n{documents_text}\n\nQuestion: {question}\n\nThink step by step. End your reply with: ANSWER: <name or yes/no> | <number>"
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            reasoning_effort="none"
        )
        answers.append(res.choices[0].message.content)
        total_usage["prompt_tokens"] += res.usage.prompt_tokens
        total_usage["completion_tokens"] += res.usage.completion_tokens
        total_usage["total_tokens"] += res.usage.total_tokens
        
    duration = time.time() - start
    return answers, total_usage, duration

def run_s3(question, max_rounds=5):
    """S3: Работа через инструменты lookup и calculate с лимитом раундов."""
    messages = [{"role": "user", "content": f"{question}\nEnd your reply with: ANSWER: <name or yes/no> | <number>"}]
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    log_steps = []
    start = time.time()
    
    for round_num in range(max_rounds):
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS_DEF,
            reasoning_effort="none"
        )
        
        usage = res.usage
        total_usage["prompt_tokens"] += usage.prompt_tokens
        total_usage["completion_tokens"] += usage.completion_tokens
        total_usage["total_tokens"] += usage.total_tokens
        
        msg = res.choices[0].message
        messages.append(msg)
        
        if not msg.tool_calls:
            break
            
        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except Exception:
                args = {}
                
            t_start = time.time()
            if func_name == "lookup":
                output = lookup(args.get("query", ""))
            elif func_name == "calculate":
                output = calculate(args.get("expression", ""))
            else:
                output = json.dumps({"error": "Unknown tool"})
            t_dur = time.time() - t_start
            
            log_steps.append({
                "round": round_num + 1,
                "tool": func_name,
                "arguments": args,
                "result": output,
                "duration": t_dur
            })
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output
            })
            
    duration = time.time() - start
    final_answer = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    return final_answer, total_usage, duration, log_steps