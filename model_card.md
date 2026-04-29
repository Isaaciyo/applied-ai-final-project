# Responsible AI Reflection

## Limitations and Biases

The biggest limitation is that the agent has no real knowledge of pet care — it's making scheduling decisions based on task labels like "medication" or "walk," not actual veterinary logic. If someone named a task "thing," the agent would treat it the same as "medication." It also doesn't know that some tasks are time-sensitive in a hard way (a diabetic pet's feeding window isn't negotiable), so when it moves a task to resolve a conflict, it's guessing based on category and priority rather than actual stakes. On top of that, the conflict detection only catches tasks at the exact same minute — two tasks that physically overlap because of duration won't get flagged.

## Could It Be Misused?

For a pet scheduling app, the misuse risk is pretty low. That said, the agent can move required task times — it won't skip them, but it could push medication from 07:30 to 09:00 without knowing why that matters. There's no guardrail that says "don't touch health tasks." The more realistic risk is exposing the API key, since anyone with it can make calls on your behalf. That's why the key lives in `.env` and is git-ignored. A future improvement would be flagging health/medication tasks as time-locked so the agent can only resolve conflicts around them, not with them.

## What Surprised Me During Testing

I expected the validation checks to always pass on clean inputs. What actually surprised me was the "required tasks included" check catching a quiet failure — when the time budget was tight and the scheduler ran out of room, a required task got silently dropped. No error, no warning, just gone from the schedule. Without that check I would have never noticed. It made me realize how easy it is to ship a scheduler that looks correct but isn't.

## Collaboration with AI

I used Claude Code throughout this project for design, debugging, and implementation. The most helpful moment was when the agent module was crashing on import because the Gemini client was being initialized at module load time — before the API key was set. Claude caught this immediately and suggested moving the client initialization inside the function call. Simple fix, but I wouldn't have found it as fast on my own.

The flawed suggestion was the original system prompt, which used numbered steps (1, 2, 3...) to tell the agent what to do. In practice, Gemini sometimes skipped steps it felt were unnecessary — it would jump straight to generating the schedule without checking for conflicts first. The fix was rewriting the prompt to be more directive and less like a numbered checklist, which made the behavior more consistent.
