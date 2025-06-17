# Missing Capability #008: Long Team Description Handling

## The Problem
Team factory crashes when team descriptions are too long because it tries to create a filename using the full description, causing "File name too long" error.

## Current State
- Team factory uses team description for filename
- No truncation or sanitization
- Crashes with detailed descriptions
- Blocks team creation

## Root Cause
Line causing issue tries to create:
```
templates/prompts/{full_team_description}_context.yaml
```

With our description, this becomes a 200+ character filename!

## Desired State
- Use team name (short) for filenames
- Or use sanitized/truncated version
- Handle long descriptions gracefully
- Don't block team creation

## Quick Fix Options
1. Use shorter team description
2. Fix the code to use team name instead
3. Add description truncation

## Long-term Fix
Team factory should:
- Use team name for all file operations
- Store full description in metadata
- Handle edge cases gracefully
- Not assume short inputs

## Impact
This blocks creating teams with proper detailed descriptions, which are needed for good agent behavior.

## Priority
HIGH - Blocking team creation
