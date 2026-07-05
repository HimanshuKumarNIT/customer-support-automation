"""
CLI Demo Script
-----------------
Runs the full pipeline (classify -> retrieve -> generate -> escalate) over
every ticket in data/sample_tickets.json and prints a readable report.

This is the fastest way to prove the whole system works end-to-end without
needing to start the API server - useful for the demo video / walkthrough.

Usage:
    python scripts/demo.py
    python scripts/demo.py --json          # machine-readable output
    python scripts/demo.py --ticket "My package never arrived, order #123"
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import process_ticket
from app.config import settings


def print_result(result_dict, use_color=True):
    c = result_dict["classification"]
    esc = result_dict["escalate"]

    def color(text, code):
        return f"\033[{code}m{text}\033[0m" if use_color else text

    urgency_color = {"high": "91", "medium": "93", "low": "92"}.get(c["urgency"], "0")

    print(color(f"\n── Ticket {result_dict['ticket_id']} ──", "1"))
    print(f"  Category:      {color(c['category'], '96')}")
    print(f"  Urgency:       {color(c['urgency'], urgency_color)}")
    print(f"  Sentiment:     {c['sentiment']}")
    print(f"  Confidence:    {c['confidence']}")
    print(f"  Classified by: {c['method']}")

    if result_dict["retrieved_articles"]:
        print("  Retrieved KB:")
        for a in result_dict["retrieved_articles"]:
            print(f"    → {a['title']}  (score={a['score']})")
    else:
        print("  Retrieved KB:  none")

    status = color("ESCALATE → HUMAN", "91") if esc else color("AUTO-RESOLVED", "92")
    print(f"  Decision:      {status}")
    if esc:
        print(f"  Reason:        {result_dict['escalation_reason']}")

    print(f"  Response ({result_dict['generation_method']}):")
    for line in result_dict["draft_response"].splitlines():
        print(f"    {line}")


def main():
    parser = argparse.ArgumentParser(description="Run the support automation demo.")
    parser.add_argument("--json", action="store_true", help="print raw JSON instead of formatted text")
    parser.add_argument("--ticket", type=str, help="process a single ad-hoc ticket message instead of the sample set")
    args = parser.parse_args()

    print(f"LLM provider: {settings.effective_provider}  |  Embedding backend: {settings.EMBEDDING_BACKEND}")

    if args.ticket:
        result = process_ticket("T-ADHOC", args.ticket).to_dict()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_result(result)
        return

    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "sample_tickets.json",
    )
    with open(data_path, "r", encoding="utf-8") as f:
        tickets = json.load(f)

    all_results = []
    for t in tickets:
        full_text = f"{t['subject']}. {t['message']}"
        result = process_ticket(t["id"], full_text).to_dict()
        all_results.append(result)
        if not args.json:
            print_result(result)

    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        escalated = sum(1 for r in all_results if r["escalate"])
        print(f"\n\n=== Summary: {len(all_results)} tickets processed, "
              f"{escalated} escalated, {len(all_results) - escalated} auto-resolved ===")


if __name__ == "__main__":
    main()
