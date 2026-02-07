---
description: Pre-task checklist - run before starting any new feature to ensure quality from the start
---

# Pre-Task Quality Checklist

Before implementing: $ARGUMENTS

## 1. Architecture Check
- Which module(s) will this feature touch?
- Read existing code in those modules first
- Identify all shared state that will be affected
- Map the thread boundaries

## 2. Required Patterns
Based on the feature, remind me to use:
- [ ] timedelta() for any date/time work
- [ ] psycopg2.sql for any new queries
- [ ] threading.Lock() for any shared state
- [ ] QThread/Worker for any blocking operations
- [ ] html.escape() for any user-displayed content
- [ ] Theme-aware colors for any UI changes
- [ ] Platform detection for any OS-specific code
- [ ] int() conversion for any Qt measurements
- [ ] finally blocks for any resource acquisition
- [ ] Specific exception handling (no bare except)

## 3. Edge Cases to Test
List the edge cases specific to this feature:
- Month/day boundaries for date features
- Empty data / None values
- Concurrent access scenarios
- Theme switching
- Window close during operation

## 4. Plan
Write the implementation plan, noting which files will change
and which patterns from above apply to each file.
