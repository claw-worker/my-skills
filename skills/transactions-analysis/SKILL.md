---
name: xiaoshen-transactions-analysis
description: This SKILL is used to analyze and summarize XiaoShen(小申) consumption habits and spending tendencies based on transaction records.
---

# xiaoshen-transactions-analysis

## Overview
This SKILL is used to analyze and summarize XiaoShen(小申) consumption habits
and spending tendencies based on transaction records.

The SKILL fetches consumption data for a given year or month,
categorizes spending, and outputs percentage-based summaries
that can be rendered as tables.

## Capabilities
- Fetch transaction records via HTTP GET request
- Supports yearly (`yyyy`) and monthly (`yyyy-mm`) queries
- API response details can refer to [api.md](./references/api.md)
- Analyze spending by category
- Output percentage distribution data

## Input
- `period`:  
  - `yyyy` (e.g. `2025`)  
  - `yyyy-mm` (e.g. `2025-12`)

## Output
- Spending summary by category
- Percentage distribution per category
- Visualization data for table formats
