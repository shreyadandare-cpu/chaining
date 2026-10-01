# Learning Notes

## What this task demonstrates

Prompt chaining splits one large task into smaller, focused steps:

1. Extract structured attributes from free text.
2. Generate multiple creative variants from those attributes.
3. Select one variant using explicit brand rules.

## Error handling lesson

Step 2 depends on Step 1. If Step 1 returns wrong or incomplete attributes, Step 2 can still run technically, but the generated copy may be based on incorrect information. Therefore each step should validate its input before passing it forward.

## What I learned

- Smaller prompts are easier to test and debug.
- Structured JSON makes one model step easier to connect to the next.
- Saving intermediate outputs makes failures traceable.
- Validation should happen between steps instead of assuming every model response is correct.
- A pipeline can complete even when an earlier step is logically wrong, so "no exception" does not always mean "correct result."
