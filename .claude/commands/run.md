---
name: run
description: Finds and executes a natural language task defined in AGENTS.md.
args:
  - task: "The name or identifier of the task inside AGENTS.md"
---

You are an automated task runner. 

Instructions:
1. Open and read the contents of the `AGENTS.md` file in the root directory.
2. Locate the specific instruction or description matching the identifier: "$task".
3. If the task is not found, stop and output an error message.
4. If found, interpret the natural language instructions provided for that task.
5. Apply those instructions directly to the current workspace or files.
6. Provide a short summary of the changes made.