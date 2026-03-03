# ADR 023: "Teach Me" Mini-Lessons — AI-Powered Topic Explanations

## Status
Accepted

## Date
2026-03-03

## Context
The existing tutor system (ADR 008) provides progressive hints and mistake explanations, but these are short and question-specific. When a student has missed a lesson on a topic (e.g. cloud types in geography), they need a more substantial explanation — like a short classroom lesson — before they can understand the question.

## Decision

### New Feature: "Teach Me" Button
A "Teach Me" button is available in two places:
1. **Question page**: "📖 I don't understand this — teach me!" link below the answer form
2. **Result page** (wrong answers only): "📖 Teach me this topic" button alongside the "Why was I wrong?" button

### Lesson Modal
Clicking the button opens a full-screen modal overlay that:
- Shows a loading spinner while the AI generates the lesson
- Displays a structured mini-lesson from Professor Quill
- Includes a "Try the Question" button to close and return to the question
- Can be closed via the button, Escape key, or clicking the backdrop

### AI Lesson Generation
- Uses GPT-4o with a dedicated system prompt (separate from hints/explanations)
- **Subject-aware**: detects maths vs geography from the skill code prefix (`geog.` → geography prompt)
- Maths lessons follow: What is it? → How does it work? (numbered steps) → Worked Example (different numbers) → Top Tips → Encouragement
- Geography lessons follow: What is it? → Key Facts (bullet points) → Real-World Example → Remember! → Encouragement
- Max 600 tokens (vs 300 for hints) to allow for proper lesson structure
- Lessons are **cached** on `QuestionInstance.lesson_html` to avoid repeat API calls

### No Gold Penalty
Unlike hints (which halve gold), lessons carry no penalty. The design philosophy is: if a student wants to learn, we should encourage that without any cost.

### Safety Rules
Same safety rules as all tutor features (ADR 008):
- Age-appropriate language (KS3)
- No personal data
- No copyrighted material
- The lesson NEVER reveals the actual question's answer (worked example uses different numbers)

### Schema Change
- New field: `QuestionInstance.lesson_html: Optional[str]` — cached lesson HTML

### Cost
- Each lesson call costs ~$0.01-0.03 (GPT-4o, 600 max tokens)
- Cached after first generation, so subsequent views are free

## Alternatives Considered
- **Pre-written lessons per template**: Too many templates (30+), high maintenance burden
- **Longer hints instead**: Hints are question-specific; lessons should teach the topic generally
- **Separate lesson pages**: Over-engineered; a modal keeps the student in context with their question
- **No caching**: Would cost more and be slower on repeat views

## Consequences
- Schema change: delete `data/app.sqlite3` before restart (new column)
- 13 new tests added to test_tutor.py (431 total)
- Easily extensible to new subjects by adding new `_LESSON_SYSTEM_*` prompts
