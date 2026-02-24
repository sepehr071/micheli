"""
Prompt package — LLM instruction templates for the voice assistant.

Module responsibilities:
    static_extraction.py      Filter extraction JSON schema (used by utils/filter_extraction.py)
    static_main_agent.py      Main agent personality + greeting template (used by agent.py)
    static_workflow.py        Sub-agent prompts for qualification flow (used by agent.py)
    dynamic_prompts.py        Category-based template selection + expert offers (used by agent.py)

Config dependencies:
    config/company.py        Company identity, products, services
    config/agents.py         Agent personality, rules, expertise
    config/prompt_settings.py Word limits, expert phrases, signal triggers
"""
