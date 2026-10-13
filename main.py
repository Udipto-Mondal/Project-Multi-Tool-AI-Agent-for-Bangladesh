import sys
import argparse
import logging

# Ensure UTF-8 output encoding across Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.agent import BangladeshAIAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEMO_QUERIES = [
    # 1. Hospital statistics query (HospitalsDBTool)
    "How many hospitals are in Dhaka?",
    # 2. General knowledge query (WebSearchTool)
    "What is the role of DGHS in Bangladesh?",
    # 3. Educational institutions query (InstitutionsDBTool)
    "How many colleges are in Dhaka?",
    # 4. Restaurant recommendations query (RestaurantsDBTool)
    "Top rated restaurants in Dhaka",
    # 5. National policy query (WebSearchTool)
    "What is the healthcare policy in Bangladesh?",
]

def run_interactive(agent: BangladeshAIAgent):
    print("=" * 65)
    print("Multi-Tool AI Agent for Bangladesh (Interactive Shell)")
    print("Type 'exit' or 'quit' to leave.")
    print("=" * 65)

    while True:
        try:
            user_input = input("\nEnter Question: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting agent. Goodbye!")
                break

            response = agent.run(user_input)
            print("\nResponse:")
            print("-" * 50)
            print(response)
            print("-" * 50)
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break

def run_demo(agent: BangladeshAIAgent):
    print("=" * 70)
    print("Executing Multi-Tool AI Agent for Bangladesh Demo Suite")
    print("=" * 70)

    for i, query in enumerate(DEMO_QUERIES, start=1):
        print(f"\n[Test Case {i}] Query: \"{query}\"")
        routed_tool = agent.route_query_offline(query)
        print(f"Target Tool: {routed_tool}")
        response = agent.run(query)
        print("Agent Response:")
        print(response)
        print("-" * 70)

def main():
    parser = argparse.ArgumentParser(description="Multi-Tool AI Agent for Bangladesh")
    parser.add_argument("--query", "-q", type=str, help="Single query to ask the agent")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive chat mode")
    parser.add_argument("--demo", "-d", action="store_true", help="Run predefined demo test cases")

    args = parser.parse_args()

    agent = BangladeshAIAgent(verbose=True)

    if args.query:
        print(agent.run(args.query))
    elif args.interactive:
        run_interactive(agent)
    else:
        # Default behavior runs demo suite
        run_demo(agent)

if __name__ == "__main__":
    main()
