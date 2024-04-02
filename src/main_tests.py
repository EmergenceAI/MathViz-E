import argparse
import csv
import json
import logging
import os

from dotenv import load_dotenv

from src.agents.math_viz_agent import MathVizAgent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Test utterances against the math vizualization agent"
        "")
    parser.add_argument(
        "--input_folder",
        type=str,
        default="tests",
        help="Folder where test files reside"
    )
    parser.add_argument(
        "--test_files",
        type=str,
        nargs="+",
        help="Csv files with test cases"
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default="tests/output",
        help="Folder to save output"
    )
    args = parser.parse_args()
    return args

def evaluate_utterances_in_file(test_file, input_folder):
    results = []
    math_viz_agent = MathVizAgent()
    with open(
        os.path.join(input_folder, test_file),
        encoding='utf-8-sig',
        newline=''
    ) as f:
        reader = csv.DictReader(f)
        curr_qid, state = None, None
        for row in reader:
            logging.info(row)
            if str(row["id"]) == curr_qid and curr_qid is not None:
                calculator_state = [json.dumps(s) for s in state]
            else:
                calculator_state = []
            expressions = math_viz_agent.process_user_request(
                row["query"],
                calculator_state
            )
            final_expr_str = None
            for expr in expressions:
                final_expr_str = expr
            final_expressions = json.loads(final_expr_str)["expressions"]
            results.append({
                "id": str(row["id"]),
                "query": row["query"],
                "ground truth": row["ground truth"],
                "output": json.dumps(final_expressions),
            })
            state, curr_qid = [e["expression"] for e in final_expressions], str(row["id"])
    return results

def output_results(results, output_folder, test_file):
    output_file = test_file.split("/")[-1].replace(".csv", "_results.csv")
    with open(os.path.join(output_folder, output_file), "w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id", "query", "ground truth", "output"
            ]
        )
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def process_file(test_file, input_folder, output_folder):
    results = []
    logging.info(f"Processing test file: {test_file}")
    try:
        results = evaluate_utterances_in_file(test_file, input_folder)
        output_results(results, output_folder, test_file)
    except Exception as e:
        logging.error(f"Error processing test file: {e}")

def main(args):
    for test_file in args.test_files:
        process_file(test_file, args.input_folder, args.output_folder)

if __name__ == "__main__":
    args = parse_args()
    load_dotenv()
    main(args)
