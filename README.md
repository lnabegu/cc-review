# cc-review - Code Review Tool for Claude Code

A human-forward CLI tool to help you review large code changes from Claude Code (or any other source). The goal is to make code review feel less like plumbing and more like something you own.

## Current Features (MVP - Phase 1)

### ✅ Diff Parsing and Display
- Parses git diffs into structured format
- Color-coded display (green for additions, red for deletions, dimmed for context)
- File-by-file organization
- Support for new files, deleted files, and renamed files
- Summary view showing total changes

## Usage

```bash
# Review changes in working tree vs HEAD
python3 cc-review.py

# Review changes against a specific commit
python3 cc-review.py HEAD~1

# Review changes against a branch
python3 cc-review.py main
```

## Example Output

```
cc-review - Code Review Tool

Fetching diff...

================================================================================
Diff Summary
================================================================================

Files changed: 2
  - Modified: 1
  - New: 1
  - Deleted: 0
Total sections: 2
================================================================================

File: routes.py
────────────────────────────────────────────────────────────────────────────────

@@ -1,14 +1,147 @@
 """
 MTA Transit API - Station Routes Module
 """
+import psycopg2
+from typing import List, Dict
 
...
```

## What's Next (Planned Features)

### Phase 2: Semantic Grouping & AI Explanations
- Use Claude API to semantically group changes across files
  - Example: "Added database layer" groups changes in routes.py, models.py, config.py
- Generate initial AI explanations for each semantic chunk
- Interactive rewriting of explanations in your own words
- These explanations become inline comments, documentation, or commit message material

### Phase 3: Ownership & Understanding
- Confidence scoring for each chunk ("Got it" / "Mostly clear" / "Need to investigate")
- Flag low-confidence sections for deeper review
- Export your explanations as inline code comments

### Phase 4: Enhanced Review Flow
- Playback mode - replay changes in logical narrative order (not chronological)
- Generate commit messages from your explanations
- Selective application of changes (finer-grained than `git add -p`)

## Why This Tool?

When Claude Code (or any AI coding assistant) generates hundreds of lines of code, it's easy to feel disconnected from your own codebase. This tool aims to:

1. **Combat alienation** - Make code feel less like "someone else's PR" and more like yours
2. **Build ownership** - The act of rewriting AI explanations helps you process and claim the logic
3. **Make review fun** - Interactive, gamified flow with progress tracking
4. **Maintain quality** - Ensure you actually understand what's being added to your codebase

## Architecture

- **Pure Python** - No external dependencies (yet)
- **Works with standard git** - Uses git diff under the hood
- **Extensible design** - Easy to add new features and integrations

## Current Implementation Details

### DiffParser
Parses standard git diff output into structured `FileDiff` and `DiffHunk` objects:
- Handles file creation/deletion/renaming
- Parses hunk headers (@@ -10,5 +10,7 @@)
- Preserves all diff content for display

### DiffDisplay
Renders diffs with ANSI color codes:
- Green for additions (+)
- Red for deletions (-)
- Dimmed for context lines
- Bold/colored headers for files and summaries

## Future Technical Additions

- Integration with Anthropic API for semantic grouping
- Local storage of review state (`.cc-review/` directory)
- Support for review sessions (pause/resume)
- Export to various formats (markdown, JSON, inline comments)

---

Built to scratch a very specific itch: making AI-generated code feel less like plumbing and more like craft.
