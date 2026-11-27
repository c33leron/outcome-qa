"""One-message local outbox for the fictional QA Desk exercise."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alias", choices=["QA-DESK"])
    parser.add_argument("question")
    args = parser.parse_args()

    question = args.question.strip()
    if not 1 <= len(question) <= 1000:
        parser.error("question must contain 1 to 1000 characters")

    receipt_path = Path(__file__).resolve().parents[1] / "qa-desk-receipt.json"
    receipt = {
        "id": "QA-DESK-001",
        "alias": args.alias,
        "recipient": "Mara Vale",
        "question": question,
        "status": "delivered_to_mock_outbox",
        "reply": None,
    }
    receipt_json = json.dumps(receipt, ensure_ascii=False)
    try:
        with receipt_path.open("x", encoding="utf-8") as outbox:
            outbox.write(receipt_json + "\n")
    except FileExistsError:
        parser.error("this trial already has a QA Desk receipt")

    print(receipt_json)


if __name__ == "__main__":
    main()
