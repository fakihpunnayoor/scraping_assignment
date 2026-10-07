# AI Usage

## Tools used
- **Claude (Anthropic)**: generated the first version of the project from the assignment brief.

## What it was used for
- Project structure, scrapers, cleaning/validation/deduplication modules, `main.py`, tests, README.

## Representative prompts
- "Complete my assignment. Simple and human." (with the assignment documents attached)

## Which parts were AI-assisted
All code and documents in the first draft. <!-- EDIT: say what YOU changed or wrote yourself -->

## Changes I made after reviewing the output
<!-- EDIT: fill in honestly after you read the code and run it. For example: things you renamed,
     simplified, or fixed, and why. -->

## Incorrect or incomplete AI suggestions I found
<!-- EDIT: e.g. selectors that didn't match the live site, a bug you hit, a wrong assumption. If you
     found none, say so. -->

## How it was tested
- 16 unit tests (cleaning, validation, deduplication) plus parser and full-pipeline tests that run against a
  fake in-memory website, including a missing element, a failed page and a duplicate record.
- <!-- EDIT: add your own live run: date, number of rows in the CSV, and that you compared the JSON counts
       with the CSV row count, and spot-checked a few rows against the websites. -->
