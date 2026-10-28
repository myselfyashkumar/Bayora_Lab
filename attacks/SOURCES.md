# Dataset sources

Built by tools/build_datasets.py (seed 42). Check each repository's license before redistributing.

| Use | Source |
| --- | --- |
| harmful_direct | AdvBench (llm-attacks/llm-attacks), HarmBench (centerforaisafety/HarmBench) |
| wrapped_jailbreak | AdvBench goals inside our own hand-written templates (dev and test use different templates) |
| wild_jailbreak | verazuo/jailbreak_llms, in-the-wild jailbreak prompts |
| prompt_extraction | hand-written |
| benign | Stanford Alpaca (tatsu-lab/stanford_alpaca, CC BY-NC 4.0) |
| benign_borderline | hand-written, normal questions that sound edgy, to measure false positives |

Splits: dev is for tuning Blue's rules, test is only for the final numbers.
