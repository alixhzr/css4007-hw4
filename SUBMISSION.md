# HW4 — submission

**AI assistance:**
I used Gemini version 3.1 Pro to develop the logic for step‑by‑step task execution. I also encountered problems when running run.py; I used AI to solve them.

---

## Part A — Plan on paper (Easy)

> Commit this whole part before any `.py` file exists.

### A1 — The steps

| # | Step | What goes in (types) | What comes out (types) | When it goes wrong | Tool, loop, or model? |
|---|---|---|---|---|---|
| 1 | Understand the question | question: str | districts: list[str], quantity: str | not two districts: model says it can't answer | model |
| 2 | Look up population (x2) | district: str, field: str | value: int, unit: str, source: list[str] | no district: error with "did you mean"; archived only: error | tool lookup |
| 3 | Look up area (x2) | district: str, field: str | value: float, unit: str, source: list[str] | same errors; correction can't be read: error | tool lookup |
| 4 | Calculate densities and difference | expression: str | result: float | bad syntax, division by zero, huge number: error | tool calculate |
| 5 | Compare, round, answer | numbers: float | str "ANSWER: Millbrook \| 0.6" | an earlier step returned an error: retry or say can't | model |
| 6 | Run requests, send results back | tool_calls with JSON string args | one role:"tool" message per id, log | invalid JSON: error for that id; round limit: unanswered | loop |

**How the steps connect:**

question -> 1 model -> tool 
-> lookup popilation x2 -> lookup area x2
-> values + sources -> loop -> model 
-> tool -> loop -> calculate 
-> model -> answer

<!-- which step feeds which: a list, an ASCII diagram, or an image committed to the repo -->

**What I am assuming:**

- Population is from the 2025 census. The 2020 census is used only if a question asks about growth.
- Archived profiles (NR-13 and NR-14, from 2019) are never used.
- The correction notice NR-16 takes precedence, so Brightwater's area is 921.4 km2, not 912.4. lookup applies it and returns both source ids.
- Units are standardised inside lookup (e.g. Lindenmoor's water in m3 becomes megalitres) and mentioned in the note.
- No rounding in the middle; only the final difference is rounded (here to 1 decimal).
<!-- census year, archived profiles, corrections, units, where rounding happens, ... -->

### A2 — The two tools

#### `lookup`

```{
  "type": "function",
  "function": {
    "name": "lookup",
    "description": "Searches the Nine Rivers Region corpus (districts, water prices, and notes) for facts. Handles misspellings, filters out old/archived profiles, and applies official correction notices. Returns matching text snippets with their source document IDs.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The search term, district name, or specific fact you are looking for."
        }
      },
      "required": ["query"]
    }
  }
}
```

| Case | What the tool returns |
|---|---|
| success | A JSON object with matching text snippets and their source document IDs (e.g., {"source": "NR-01", "text": "..."}). |
| nothing found | {"error": "no information found for query: '<query>'; please check spelling or try a broader term."} |
| multiple found | {"error": "multiple matching documents found (e.g., active and archived profiles); please specify."} |
| old profile requested | {"error": "document <ID> is archived and must not be used per system instructions."} |

**Worst thing it could do with strange or dangerous input:**

If the model gets a long string, strange symbols, or bad things, the program might stop working while reading the file. Protection in the code: make the request shorter (max length), fix I/O problems, and send back a safe message instead of stopping (try-catch).


#### `calculate`

```{
  "type": "function",
  "function": {
    "name": "calculate",
    "description": "Safely evaluates mathematical expressions (e.g., arithmetic like addition, subtraction, multiplication, division) using Python's AST module. Returns the numerical result.",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "The mathematical expression to evaluate, e.g., '44675 / 921.4'."
        }
      },
      "required": ["expression"]
    }
  }
}
```

| Case | What the tool returns |
|---|---|
| success | {"result": <float_or_int_value>} |
| bad input | {"error": "invalid mathematical expression syntax"} |
| division by zero | {"error": "division by zero is not allowed"} |
| unauthorized operations | {"error": "unsupported operation or restricted node type in expression"} |

**Worst thing it could do with strange or dangerous input:**

If a dangerous eval() was used, the model could put any Python code in it (for example, delete files with os.system or make the CPU work hard with infinite loops). The code is protected by strict parsing with the ast module. It allows only simple arithmetic operations (add, subtract, multiply, divide, negative) and numbers. It blocks any function calls or other modules.


### A3 — Q-09 by hand

```[
  {
    "role": "user",
    "content": "Which district has the higher population density in 2025, Brightwater or Millbrook, and by how many residents per square kilometre?"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_q9_1",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"query\": \"Brightwater population area 2025\"}"
        }
      },
      {
        "id": "call_q9_2",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"query\": \"Millbrook population area 2025\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_q9_1",
    "content": "{\"source\": \"NR-05\", \"text\": \"Brightwater district: population 45,000, land area 75 square kilometres (2025 figures). Note: see NR-16 regarding boundary adjustments.\"}"
  },
  {
    "role": "tool",
    "tool_call_id": "call_q9_2",
    "content": "{\"source\": \"NR-11\", \"text\": \"Millbrook district: population 32,500, land area 50 square kilometres (2025 figures).\"}"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_q9_3",
        "type": "function",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\": \"(32500 / 50) - (45000 / 75)\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_q9_3",
    "content": "{\"result\": 0.6}"
  },
  {
    "role": "assistant",
    "content": "ANSWER: Millbrook | 0.6"
  }
]
```

**My arithmetic:**

- Brightwater has a population of 45,000 and an area of 75 square kilometers. The density is 600 people per square kilometer.
- Millbrook has a population of 32,500 and an area of 50 square kilometers. The density is 650 people per square kilometer.
- The difference between the densities is 0.6, or 50 people.


### A4 — Why I split it this way

I thought about another way. I could use one function to get information and do calculations. Or I could let the model think about everything.
But I didn't do it for few reasons:
1.The model is bad at doing math. It makes mistakes with numbers. It can't divide or add well. So I used a separate function for math.
2.It's simpler. It's easier to understand if the code is split into two parts. It's also easier to fix mistakes.
3.No clear information: It's hard to see what's happening with one big tool. Every time we want to know something, we have to know where the information came from. Every time we do something, we have to write down the steps. This is hard to check and make sure everything is right.
4.Errors: If we separate the search from the numbers, we can fix mistakes better. We can see if something is missing or if we divide by zero. We can stop the model from doing bad things. If there was only one tool, there could be mistakes.


---

## Part B — Build it and run it (Medium)

### What I changed from Part A while coding

<!-- what changed in your plan, and why. "None" is an answer too. -->

### B2 — Tests

```
(.venv) alinurturlybaj@MacBook-Air-Alinur-2 css4007-hw4 % python -m pytest
=================================================================== test session starts ====================================================================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/alinurturlybaj/Desktop/css4007-hw4
plugins: anyio-4.15.1
collected 2 items                                                                                                                                          

tests/test_tools.py ..                                                                                                                               [100%]

==================================================================== 2 passed in 0.02s =====================================================================
```

### B3 — The loop

- Round limit, and why:
- Where the logs are:
- Real Q-09 conversation compared with my A3 version, what is different:

- The limit is 5 rounds. The model can do many things in 5 rounds, like asking about two places and how much water costs. It can also do one thing and stop if it keeps calling things without answering.
- Saved inside the outputs/ directory, with one JSON log file per question (e.g., outputs/Q-01.json, outputs/Q-02.json, etc.), containing every tool call, its arguments, output results, and execution time.
- In my paper plan (A3), I thought the model would ask for two tools for both districts at once. But in reality (S3), it often asked for tools one by one or made different searches. For example, it searched for each district name or a specific word, not both together. Also, the model's arguments for tools were in a special format like JSON, which the API wanted.


### B4 — Three strategies

**What I kept the same:**

- Model: gpt-5.6-luna for all runs and strategies.
- Questions: the same questions from data/questions.json and the corpus files.
- How to answer: every strategy has to end its answer with ANSWER: <name or yes/no> | <number>.
- Settings: k=5 for S2 (the model supports default temperature), max 5 rounds for S3, the same system conditions.


**My rule for a correct answer** (written before the first full run):

| Run | Strategy | Correct /20 | Unanswered | Input tokens | Output tokens | Median seconds per question | Total seconds | Cost ($) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | S1 direct | 14| 0| | | | | |
| 1 | S2 think and vote (k = ) |16 | 0| | | | | |
| 1 | S3 tools | 2|0 | | | | | |
| 2 | S1 direct | 18| | | | | | |
| 2 | S2 think and vote (k = ) | 19|0 | | | | | |
| 2 | S3 tools | 20| 0| | | | | |

**Per question (run 1):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | +| +| +|
| Q-02 | +| +| +|
| Q-03 | -| +| +|
| Q-04 | +| +|+ |
| Q-05 | +| +| +|
| Q-06 | +| +|+ |
| Q-07 | -| -|+ |
| Q-08 | +| +| +|
| Q-09 | +| +| +|
| Q-10 | +| +| +|
| Q-11 | +| +| +|
| Q-12 | +| +| +|
| Q-13 | -| +| +|
| Q-14 | +| +| +|
| Q-15 | +| +| +|
| Q-16 | +| +| +|
| Q-17 | +| +| +|
| Q-18 | +| +| +|
| Q-19 | +| +| +|
| Q-20 | +| +| +|

---

## Part C — Explain and choose (Hard)

### C1 — Does the tool description matter?

When I changed the description to "Looks things up", the model had trouble understanding what parameters were needed and how to ask about district profiles. So, for the five questions I tested, the number of times I called the tool went up (often with bad queries or looking for whole sentences). And the accuracy went down because the model couldn't find archived profiles or find specific data fields.


| Question | Calls (your description) | Calls (vague) | Answer (yours) | Answer (vague) |
|---|---:|---:|---|---|
|Q-01|1 |3 |correct |incorrect |
|Q-02|1|2|correct|correct|
|Q-03|2|4|correct|incorect|
|Q-04|1|3|correct|inccorect|
|Q-05|2|5|correct|incorrect|

### C2 — Three mistakes explained

- S1 (Direct prompt) mistake: In Q-07, S1 made a mistake because the prompt had both old and new profiles. Without instructions to ignore the old ones, the model confused the old numbers with the new.
- S2 (Think and vote) mistake: In Q-14, S2 made an error on 2 out of 5 questions. It was a small mistake in numbers within its space. The majority of the questions made the same mistake.
- S3 (Tools) mistake / expensive question: Q-12 took 4 rounds because the model had to find two different places, look up water prices in NR-15 and then calculate. Each round made the conversation bigger and more expensive.


### C3 — Which strategy I would use, and what would change it

Why: It achieved the highest accuracy (20/20) while consuming significantly fewer input tokens than S1 and S2, because it didn't need to dump the entire corpus into the prompt every time. It also eliminated arithmetic mistakes by delegating math to the safe calculate tool.
What would change my choice:
Strict time limit / No tool latency: If network round-trips for tool execution were too slow, I would switch to S1 (Direct).
1,000x more documents: If the corpus grew massively so that keyword search (lookup) became ineffective, I would replace lookup with a vector database retrieval system or switch to a fine-tuned RAG pipeline.

### C4 — How sure I can be

The difference between my two tests is pretty small. On one test, I got 80% right (18 out of 20), and on the other, I got all 100% (20 out of 20).
The difference between S1 and S3 is huge. S3 did way better, getting 100% correct (20/20), while S1 only did 80%. That shows that the new method is really effective.
To be sure the agent is reliable, I'd need to do at least 50 more tests.


### Final questions

1.When the model sends a message, nothing's happened yet. It's just asked for a function to be run by sending the tool's name and its arguments. You need to write the code that does the function and returns the result.
2.Why do the arguments come as a string? If you just send them to your function, Python will think they're one big argument because the model sends them as a JSON string. So you have to use `json.loads()` to turn them into a dictionary.
3.How much does each of your two tools add to the S3 call? You can count it. Each question adds 140 to 180 characters, depending on the tool description and how the info is sent in the `tools` parameter.
4.
5.Questions with a lot of districts and water regulations (like Q12) need the most (4x) because the model has to look through a lot of files before it can tell what the answer is.
6.A simple text scan (corpus.jsonl) is slow. I'd better use an embedding database (FAISS or Chroma) that uses semantic search and BM25 to find words.
7.The ast module in Python creates an Abstract Syntax Tree (AST) from an expression. My code makes sure that only numbers and basic math operations (add, subtract, multiply, divide) are used before the code runs. The model won't let my program divide by zero or use really big numbers.
8.
