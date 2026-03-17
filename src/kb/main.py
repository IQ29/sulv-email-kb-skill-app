"""
Enterprise Knowledge AI Platform - Main CLI
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipelines.ingestion import IngestionPipeline
from src.pipelines.query import QueryPipeline
from src.pipelines.report import ReportGenerator


def load_config():
    """Load configuration from file."""
    config_path = Path(__file__).parent / "config" / "pipeline.yaml"
    
    # For now, use default config
    # In production, parse YAML
    return {
        "storage": {"base_path": "./data"},
        "performance": {
            "chunk_size": 512,
            "chunk_overlap": 50,
            "top_k_retrieval": 10,
            "batch_size": 16
        },
        "pipeline": {
            "ingestion": {
                "embedder": "minilm"
            }
        },
        "api_fallback": {
            "provider": "kimi",
            "model": "kimi-k2.5",
            "max_tokens": 500
        }
    }


def cmd_ingest(args):
    """Ingest a file or directory."""
    config = load_config()
    config["user"] = args.user
    
    pipeline = IngestionPipeline(config)
    
    path = Path(args.path)
    
    if path.is_file():
        print(f"Ingesting: {path}")
        result = pipeline.process_file(str(path), {"user": args.user, "source": args.source})
        print(json.dumps(result, indent=2))
        
    elif path.is_dir():
        files = list(path.glob("*"))
        print(f"Found {len(files)} files in {path}")
        
        for file_path in files:
            if file_path.is_file():
                print(f"\nIngesting: {file_path.name}")
                result = pipeline.process_file(str(file_path), {"user": args.user, "source": args.source})
                print(f"  Success: {result['success']}")
                if result['success']:
                    print(f"  Chunks: {result['steps'].get('chunk', {}).get('num_chunks', 0)}")
    
    else:
        print(f"Error: Path not found: {path}")
        return 1
    
    return 0


def cmd_query(args):
    """Query the knowledge base."""
    config = load_config()
    config["user"] = args.user
    
    pipeline = QueryPipeline(config)
    
    print(f"Query: {args.question}")
    print("-" * 50)
    
    result = pipeline.query(args.question)
    
    if result["success"]:
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources ({len(result['sources'])}):")
        for src in result['sources']:
            meta = src.get('metadata', {})
            print(f"  - {meta.get('source_file', 'Unknown')} (score: {src.get('score', 0):.3f})")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return 0


def cmd_chat(args):
    """Interactive chat mode."""
    config = load_config()
    config["user"] = args.user
    
    pipeline = QueryPipeline(config)
    
    print("Enterprise Knowledge AI - Chat Mode")
    print("Type 'quit' or 'exit' to end")
    print("-" * 50)
    
    while True:
        try:
            question = input("\nYou: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            result = pipeline.query(question)
            
            if result["success"]:
                print(f"\nAI: {result['answer']}")
            else:
                print(f"\nAI: Sorry, I encountered an error: {result.get('error')}")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
    
    return 0


def cmd_report(args):
    """Generate reports."""
    config = load_config()
    config["user"] = args.user
    
    generator = ReportGenerator(config)
    
    if args.type == "daily":
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        print(f"Generating daily report for {date}...")
        report = generator.generate_daily_report(date, args.user)
        print(f"Report saved. Documents: {report['summary']['total_documents']}")
        
    elif args.type == "weekly":
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        print(f"Generating weekly report for week of {date}...")
        report = generator.generate_weekly_report(date, args.user)
        print(f"Report saved. Documents: {report['summary']['total_documents']}")
        
    elif args.type == "monthly":
        month = args.date or datetime.now().strftime("%Y-%m")
        print(f"Generating monthly report for {month}...")
        report = generator.generate_monthly_report(month, args.user)
        print(f"Report saved. Documents: {report['summary']['total_documents']}")
    
    return 0


def cmd_stats(args):
    """Show system statistics."""
    config = load_config()
    
    pipeline = IngestionPipeline(config)
    stats = pipeline.get_stats()
    
    print("System Statistics")
    print("-" * 50)
    print(f"Vector DB: {stats['vectordb']['document_count']} documents")
    print(f"Embedder: {stats['embedder']['name']}")
    print(f"Embedder RAM: {stats['embedder']['ram_usage_mb']} MB")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Knowledge AI Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a file
  python main.py ingest ~/Documents/contract.pdf --user john
  
  # Ingest a directory
  python main.py ingest ~/Documents/inbox/ --source gmail --user john
  
  # Query
  python main.py query "What contracts were signed last week?" --user john
  
  # Interactive chat
  python main.py chat --user john
  
  # Generate report
  python main.py report daily --date 2026-03-14 --user john
  
  # Show stats
  python main.py stats
        """
    )
    
    parser.add_argument("--user", default="default", help="User identifier")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest files")
    ingest_parser.add_argument("path", help="File or directory to ingest")
    ingest_parser.add_argument("--source", default="manual", help="Source identifier")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query knowledge base")
    query_parser.add_argument("question", help="Query question")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument("type", choices=["daily", "weekly", "monthly"])
    report_parser.add_argument("--date", help="Date for report (YYYY-MM-DD or YYYY-MM)")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show system statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handler
    commands = {
        "ingest": cmd_ingest,
        "query": cmd_query,
        "chat": cmd_chat,
        "report": cmd_report,
        "stats": cmd_stats
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
