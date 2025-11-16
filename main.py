"""
Personal Research Concierge Agent - PRODUCTION VERSION
Multi-agent research system using Google ADK with full CLI support
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import time
from google import genai
from dotenv import load_dotenv
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents import (
    UserIntentAgent,
    WebSearchAgent,
    PDFDocumentAgent,
    SourceSummarizerAgent,
    FactCheckAgent,
    SynthesisAgent,
    QualityLoopAgent
)
from src.schemas import ResearchBrief
from src.memory import memory_bank, session_manager
from src.utils import setup_logging, trace_context

import logging

# Load environment variables
load_dotenv()


class ResearchConciergeOrchestrator:
    """
    PRODUCTION-GRADE orchestrator for the Personal Research Concierge
    Coordinates all agents with full error handling and observability
    """

    def __init__(self, api_key: str = None, log_level: str = "INFO"):
        """
        Initialize the orchestrator

        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        # Setup logging
        log_file = os.getenv("LOG_FILE", "logs/research_concierge.log")
        setup_logging(log_level=log_level, log_file=log_file)
        self.logger = logging.getLogger(__name__)

        self.logger.info("=" * 80)
        self.logger.info("Personal Research Concierge Agent - PRODUCTION MODE")
        self.logger.info("=" * 80)

        # Initialize Google GenAI client
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            self.logger.error(
                "❌ No GOOGLE_API_KEY found! Please set it in .env file or environment."
            )
            print("\n⚠️  SETUP REQUIRED:")
            print("   1. Get API key from: https://aistudio.google.com/app/apikey")
            print("   2. Copy .env.example to .env")
            print("   3. Add your GOOGLE_API_KEY to .env")
            print("   4. Run again\n")
            sys.exit(1)

        try:
            self.client = genai.Client(api_key=api_key)
            self.logger.info("✓ Google GenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize GenAI client: {str(e)}")
            raise

        # Initialize all agents
        self.logger.info("Initializing 7 intelligent agents...")

        self.user_intent_agent = UserIntentAgent(self.client)
        self.web_search_agent = WebSearchAgent(self.client)
        self.pdf_agent = PDFDocumentAgent(self.client)
        self.summarizer_agent = SourceSummarizerAgent(self.client)
        self.fact_check_agent = FactCheckAgent(self.client)
        self.synthesis_agent = SynthesisAgent(self.client)
        self.quality_loop_agent = QualityLoopAgent(self.client)

        self.logger.info("✓ All 7 agents initialized successfully")

    def research(
        self,
        user_query: str,
        pdf_files: Optional[List[str]] = None,
        max_sources: int = 10,
        save_memory: bool = True
    ) -> ResearchBrief:
        """
        Execute full research pipeline

        Args:
            user_query: User's research query
            pdf_files: Optional list of PDF file paths to analyze
            max_sources: Maximum number of web sources to gather
            save_memory: Whether to export memory to JSON

        Returns:
            Final ResearchBrief
        """
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info(f"RESEARCH QUERY: {user_query}")
        self.logger.info(f"{'=' * 80}\n")

        # Start trace
        trace_id = f"research_{int(time.time())}"
        trace_context.start_trace(trace_id, "full_research", {"query": user_query})

        # Create session
        session_id = f"session_{int(time.time())}"
        session_manager.create_session(session_id, {"query": user_query})

        start_time_total = time.time()

        try:
            # ==================================================================
            # STEP 1: User Intent Analysis
            # ==================================================================
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("STEP 1/6: Analyzing User Intent")
            self.logger.info(f"{'=' * 80}")

            start_time = time.time()
            user_intent = self.user_intent_agent.analyze_intent(user_query)
            duration = time.time() - start_time

            trace_context.add_event("intent_analyzed", {
                "topic": user_intent.topic,
                "scope": user_intent.scope.value,
                "duration": duration
            })

            self.logger.info(f"✓ Intent analyzed in {duration:.2f}s")
            self.logger.info(f"  • Topic: {user_intent.topic}")
            self.logger.info(f"  • Scope: {user_intent.scope.value}")
            self.logger.info(f"  • Style: {user_intent.style.value}")
            self.logger.info(f"  • Keywords: {', '.join(user_intent.keywords[:5])}")

            # ==================================================================
            # STEP 2: Parallel Research (Web + PDF)
            # ==================================================================
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("STEP 2/6: Gathering Sources (Parallel)")
            self.logger.info(f"{'=' * 80}")

            # Web Search
            self.logger.info("→ Web Search Agent working...")
            start_time = time.time()

            search_queries = [user_intent.topic] + user_intent.keywords[:2]
            web_results = []

            for idx, query in enumerate(search_queries[:3], 1):
                self.logger.info(f"  Searching: '{query}' ({idx}/3)")
                result = self.web_search_agent.search(query, num_results=max_sources // 3)
                web_results.append(result)

            web_duration = time.time() - start_time
            total_urls = sum(len(r.urls) for r in web_results)

            trace_context.add_event("web_search_completed", {
                "num_queries": len(search_queries),
                "total_urls": total_urls,
                "duration": web_duration
            })

            self.logger.info(f"✓ Web search completed in {web_duration:.2f}s")
            self.logger.info(f"  • Found {total_urls} URLs across {len(web_results)} queries")

            # PDF Processing
            doc_analyses = []
            if pdf_files:
                self.logger.info(f"\n→ PDF Agent processing {len(pdf_files)} documents...")
                start_time = time.time()

                for idx, pdf_file in enumerate(pdf_files, 1):
                    self.logger.info(f"  Processing: {Path(pdf_file).name} ({idx}/{len(pdf_files)})")
                    analysis = self.pdf_agent.process_document(pdf_file, session_id)
                    doc_analyses.append(analysis)

                    if analysis.get("success"):
                        self.logger.info(f"    ✓ Extracted {analysis.get('word_count', 0)} words")
                    else:
                        self.logger.warning(f"    ⚠ Failed: {analysis.get('error', 'Unknown error')}")

                pdf_duration = time.time() - start_time
                trace_context.add_event("pdf_processing_completed", {
                    "num_files": len(pdf_files),
                    "duration": pdf_duration
                })

                self.logger.info(f"✓ PDF processing completed in {pdf_duration:.2f}s")

            # ==================================================================
            # STEP 3: Source Summarization
            # ==================================================================
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("STEP 3/6: Summarizing Sources")
            self.logger.info(f"{'=' * 80}")

            start_time = time.time()
            all_summaries = self.summarizer_agent.summarize_all_sources(
                web_results, doc_analyses
            )
            summarize_duration = time.time() - start_time

            # Calculate average reliability
            avg_reliability = sum(s.reliability_score for s in all_summaries) / len(all_summaries) if all_summaries else 0

            trace_context.add_event("summarization_completed", {
                "num_summaries": len(all_summaries),
                "avg_reliability": avg_reliability,
                "duration": summarize_duration
            })

            self.logger.info(f"✓ Summarization completed in {summarize_duration:.2f}s")
            self.logger.info(f"  • Created {len(all_summaries)} source summaries")
            self.logger.info(f"  • Average reliability score: {avg_reliability:.1f}/100")

            # ==================================================================
            # STEP 4: Fact-Checking
            # ==================================================================
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("STEP 4/6: Fact-Checking Claims")
            self.logger.info(f"{'=' * 80}")

            start_time = time.time()
            fact_checks = self.fact_check_agent.check_all_claims(all_summaries)
            contradictions = self.fact_check_agent.find_contradictions(all_summaries)
            factcheck_duration = time.time() - start_time

            verified = sum(1 for fc in fact_checks if fc.verdict == "True")
            unverified = sum(1 for fc in fact_checks if fc.verdict == "Unverified")

            trace_context.add_event("fact_checking_completed", {
                "num_checks": len(fact_checks),
                "verified": verified,
                "unverified": unverified,
                "num_contradictions": len(contradictions),
                "duration": factcheck_duration
            })

            self.logger.info(f"✓ Fact-checking completed in {factcheck_duration:.2f}s")
            self.logger.info(f"  • Verified: {verified}/{len(fact_checks)} claims")
            self.logger.info(f"  • Found {len(contradictions)} contradictions")

            # ==================================================================
            # STEP 5: Synthesis
            # ==================================================================
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("STEP 5/6: Synthesizing Research Brief")
            self.logger.info(f"{'=' * 80}")

            start_time = time.time()
            initial_brief = self.synthesis_agent.synthesize(
                all_summaries, fact_checks, contradictions
            )
            synthesis_duration = time.time() - start_time

            trace_context.add_event("synthesis_completed", {"duration": synthesis_duration})

            self.logger.info(f"✓ Synthesis completed in {synthesis_duration:.2f}s")
            self.logger.info(f"  • Executive summary: {len(initial_brief.executive_summary)} chars")
            self.logger.info(f"  • Top insights: {len(initial_brief.top_insights)}")
            self.logger.info(f"  • Evidence entries: {len(initial_brief.evidence_table)}")

            # ==================================================================
            # STEP 6: Quality Loop
            # ==================================================================
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("STEP 6/6: Quality Improvement Loop")
            self.logger.info(f"{'=' * 80}")

            start_time = time.time()
            final_brief = self.quality_loop_agent.evaluate_and_improve(initial_brief)
            quality_duration = time.time() - start_time

            iterations = memory_bank.get_iterations()
            final_score = iterations[-1]["quality_score"] if iterations else 0

            trace_context.add_event("quality_loop_completed", {
                "iterations": len(iterations),
                "final_score": final_score,
                "duration": quality_duration
            })

            self.logger.info(f"✓ Quality loop completed in {quality_duration:.2f}s")
            self.logger.info(f"  • Iterations: {len(iterations)}")
            self.logger.info(f"  • Final Quality Score: {final_score}/100")

            # ==================================================================
            # COMPLETION
            # ==================================================================
            total_duration = time.time() - start_time_total

            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("✅ RESEARCH COMPLETE!")
            self.logger.info(f"{'=' * 80}")
            self.logger.info(f"Total Time: {total_duration:.2f}s ({total_duration / 60:.1f} minutes)")
            self.logger.info(f"Quality Score: {final_score}/100")
            self.logger.info(f"Total Sources: {len(all_summaries)}")
            self.logger.info(f"{'=' * 80}\n")

            # End trace
            trace_context.end_trace("success", {
                "brief_length": len(final_brief.executive_summary),
                "total_duration": total_duration
            })

            # Export memory if requested
            if save_memory:
                memory_file = f"outputs/memory_{session_id}.json"
                Path(memory_file).parent.mkdir(parents=True, exist_ok=True)
                memory_bank.export_to_json(memory_file)
                self.logger.info(f"Memory exported to: {memory_file}")

            # Close session
            session_manager.close_session(session_id)

            return final_brief

        except KeyboardInterrupt:
            self.logger.warning("\n⚠️  Research interrupted by user (Ctrl+C)")
            trace_context.end_trace("interrupted")
            session_manager.pause_session(session_id)
            raise
        except Exception as e:
            self.logger.error(f"\n❌ Research pipeline failed: {str(e)}", exc_info=True)
            trace_context.end_trace("error", {"error": str(e)})
            session_manager.close_session(session_id)
            raise

    def export_brief(self, brief: ResearchBrief, output_file: str):
        """
        Export research brief to formatted text file

        Args:
            brief: ResearchBrief to export
            output_file: Output file path
        """
        self.logger.info(f"Exporting brief to {output_file}")

        output = []
        output.append("=" * 80)
        output.append("PERSONAL RESEARCH CONCIERGE - RESEARCH BRIEF")
        output.append("=" * 80)
        output.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 80)
        output.append("")

        # Executive Summary
        output.append("EXECUTIVE SUMMARY")
        output.append("-" * 80)
        output.append(brief.executive_summary)
        output.append("")

        # Top 10 Insights
        output.append("TOP 10 INSIGHTS")
        output.append("-" * 80)
        for i, insight in enumerate(brief.top_insights, 1):
            output.append(f"{i}. {insight}")
        output.append("")

        # Evidence Table
        output.append("EVIDENCE TABLE")
        output.append("-" * 80)
        for i, evidence in enumerate(brief.evidence_table[:20], 1):
            output.append(f"\n[{i}] {evidence.claim}")
            output.append(f"    Evidence: {evidence.evidence[:300]}...")
            output.append(f"    Source: {evidence.source_url}")
            output.append(f"    Reliability: {evidence.reliability_score}/100")
            output.append(f"    Type: {evidence.source_type}")
        output.append("")

        # Contradictions
        if brief.contradictions:
            output.append("CONTRADICTIONS FOUND")
            output.append("-" * 80)
            for i, contradiction in enumerate(brief.contradictions, 1):
                output.append(f"{i}. {contradiction}")
            output.append("")

        # Data Points
        if brief.data_points:
            output.append("KEY DATA POINTS")
            output.append("-" * 80)
            for i, point in enumerate(brief.data_points, 1):
                output.append(f"{i}. {point}")
            output.append("")

        # Glossary
        if brief.glossary:
            output.append("GLOSSARY")
            output.append("-" * 80)
            for term, definition in brief.glossary.items():
                output.append(f"• {term}: {definition}")
            output.append("")

        # Suggested Reading
        output.append("SUGGESTED READING")
        output.append("-" * 80)
        for i, reading in enumerate(brief.suggested_reading, 1):
            output.append(f"{i}. {reading}")
        output.append("")

        # Next Questions
        output.append("NEXT RESEARCH QUESTIONS")
        output.append("-" * 80)
        for i, question in enumerate(brief.next_questions, 1):
            output.append(f"{i}. {question}")
        output.append("")

        output.append("=" * 80)
        output.append("End of Research Brief")
        output.append("=" * 80)

        # Write to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(output))

        file_size = Path(output_file).stat().st_size
        self.logger.info(f"✓ Brief exported successfully ({file_size:,} bytes)")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Personal Research Concierge - AI-Powered Research Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with query
  python main.py "What are the latest trends in quantum computing?"

  # With PDF files
  python main.py "AI ethics" --pdfs paper1.pdf paper2.pdf

  # Custom output file
  python main.py "Climate change" --output my_research.txt

  # More sources and verbose logging
  python main.py "Machine learning" --max-sources 20 --verbose

  # Non-interactive mode (for scripting)
  python main.py "Blockchain technology" --no-interactive

For more information, see README.md
        """
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="Research query (if not provided, will prompt interactively)"
    )

    parser.add_argument(
        "--pdfs",
        nargs="+",
        help="PDF files to analyze (space-separated paths)"
    )

    parser.add_argument(
        "--output", "-o",
        default="outputs/research_brief.txt",
        help="Output file path (default: outputs/research_brief.txt)"
    )

    parser.add_argument(
        "--max-sources",
        type=int,
        default=10,
        help="Maximum number of web sources to gather (default: 10)"
    )

    parser.add_argument(
        "--api-key",
        help="Google API key (overrides environment variable)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )

    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Non-interactive mode (exit on errors)"
    )

    parser.add_argument(
        "--save-memory",
        action="store_true",
        default=True,
        help="Export memory to JSON (default: True)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Personal Research Concierge v1.0.0"
    )

    return parser.parse_args()


def main():
    """Main entry point with CLI support"""
    print("=" * 80)
    print("Personal Research Concierge Agent")
    print("AI-Powered Multi-Agent Research System")
    print("=" * 80)
    print()

    args = parse_arguments()

    # Get query (interactive if not provided)
    if args.query:
        user_query = args.query
    elif args.no_interactive:
        print("❌ Error: Query required in non-interactive mode")
        print("Usage: python main.py \"your research query\"")
        sys.exit(1)
    else:
        print("Enter your research query:")
        user_query = input("> ").strip()
        if not user_query:
            print("❌ Error: Empty query")
            sys.exit(1)

    # Set log level
    log_level = "DEBUG" if args.verbose else "INFO"

    print(f"\n🔬 Research Query: {user_query}")
    if args.pdfs:
        print(f"📄 PDF Files: {len(args.pdfs)}")
    print(f"🎯 Max Sources: {args.max_sources}")
    print(f"💾 Output: {args.output}")
    print()

    try:
        # Initialize orchestrator
        orchestrator = ResearchConciergeOrchestrator(
            api_key=args.api_key,
            log_level=log_level
        )

        # Execute research
        brief = orchestrator.research(
            user_query=user_query,
            pdf_files=args.pdfs,
            max_sources=args.max_sources,
            save_memory=args.save_memory
        )

        # Export results
        orchestrator.export_brief(brief, args.output)

        print()
        print("=" * 80)
        print(f"✅ SUCCESS! Research brief saved to: {args.output}")
        print("=" * 80)
        print()

        # Print summary
        print("BRIEF SUMMARY:")
        print(brief.executive_summary[:500] + "..." if len(brief.executive_summary) > 500 else brief.executive_summary)
        print()
        print(f"📊 Statistics:")
        print(f"  • Total Sources: {len(brief.evidence_table)}")
        print(f"  • Top Insights: {len(brief.top_insights)}")
        print(f"  • Contradictions: {len(brief.contradictions)}")
        print(f"  • Data Points: {len(brief.data_points)}")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
