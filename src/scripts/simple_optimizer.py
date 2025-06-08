#!/usr/bin/env python3
"""
Simple Prompt Optimization CLI

This script provides command-line utilities for optimizing prompts based on chat feedback.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from simple_prompt_optimizer import SimplePromptOptimizer, OptimizationRequest

def list_performance():
    """List performance summary for all agents"""
    optimizer = SimplePromptOptimizer()
    
    print("📊 Agent Performance Summary")
    print("=" * 60)
    
    # Get all agent configs
    etc_dir = Path("etc")
    agent_files = [f.stem for f in etc_dir.glob("*.toml") 
                   if f.name not in ["config.toml", "prompt_optimizer_agent.toml"]]
    
    for agent_name in agent_files:
        performance = optimizer.get_agent_performance_summary(agent_name)
        
        print(f"\n🤖 {agent_name}")
        print(f"   Sessions: {performance['sessions']}")
        if performance['rated_sessions'] > 0:
            print(f"   Average Rating: {performance['average_rating']:.1f}/5")
            print(f"   Low-rated: {performance['low_rated_count']}")
            if performance['needs_optimization']:
                print(f"   Status: ⚠️  Needs optimization")
            else:
                print(f"   Status: ✅ Performing well")
        else:
            print(f"   Status: 📝 No ratings yet")

def list_candidates():
    """List agents that need optimization"""
    optimizer = SimplePromptOptimizer()
    candidates = optimizer.list_optimization_candidates()
    
    print("🚀 Optimization Candidates")
    print("=" * 50)
    
    if not candidates:
        print("✅ No agents need optimization - all performing well!")
        return
    
    for candidate in candidates:
        agent_name = candidate["agent_name"]
        performance = candidate["performance"]
        
        print(f"\n⚠️  {agent_name}")
        print(f"   Average Rating: {performance['average_rating']:.1f}/5")
        print(f"   Sessions: {performance['sessions']}")
        print(f"   Low-rated: {performance['low_rated_count']}")
        print(f"   Suggested Goals: {', '.join(candidate['suggested_goals'])}")
        print(f"   Sessions to analyze: {len(candidate['low_rated_sessions'])}")

async def optimize_agent(agent_name: str, auto: bool = False):
    """Optimize a specific agent"""
    optimizer = SimplePromptOptimizer()
    
    # Check if agent needs optimization
    candidates = optimizer.list_optimization_candidates()
    agent_candidate = next((c for c in candidates if c["agent_name"] == agent_name), None)
    
    if not agent_candidate:
        performance = optimizer.get_agent_performance_summary(agent_name)
        if performance["sessions"] == 0:
            print(f"❌ No sessions found for {agent_name}")
        else:
            print(f"✅ {agent_name} is performing well (avg: {performance['average_rating']:.1f}/5)")
        return
    
    print(f"🔧 Optimizing {agent_name}...")
    
    # Get low-rated sessions
    low_sessions = optimizer.get_low_rated_sessions(agent_name)
    
    if not low_sessions:
        print(f"❌ No low-rated sessions found for {agent_name}")
        return
    
    print(f"   Analyzing {len(low_sessions)} low-rated sessions")
    print(f"   Goals: {', '.join(agent_candidate['suggested_goals'])}")
    
    if not auto:
        # Ask for confirmation
        print("\nLow-rated sessions:")
        for session in low_sessions:
            print(f"   ⭐ {session['rating']}/5 - {session['name'][:50]}...")
            if session['notes']:
                print(f"     Notes: {session['notes'][:100]}...")
        
        response = input("\nProceed with optimization? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            print("Optimization cancelled")
            return
    
    # Create optimization request
    request = OptimizationRequest(
        agent_name=agent_name,
        target_sessions=[s["session_id"] for s in low_sessions[:3]],  # Max 3 sessions
        optimization_goals=agent_candidate["suggested_goals"],
        notes="CLI optimization based on low-rated sessions"
    )
    
    try:
        new_file = await optimizer.optimize_prompt(request)
        print(f"✅ Created new version: {new_file}")
        print("\n💡 Next steps:")
        print(f"   1. Review the new file: etc/{new_file}")
        print(f"   2. Test the optimized prompt")
        print(f"   3. If satisfied, replace the original: mv etc/{new_file} etc/{agent_name}.toml")
        print(f"   4. Commit to git: git add etc/{agent_name}.toml && git commit -m 'Optimize {agent_name} prompt'")
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

async def auto_optimize_all():
    """Automatically optimize all candidates"""
    optimizer = SimplePromptOptimizer()
    candidates = optimizer.list_optimization_candidates()
    
    if not candidates:
        print("✅ No agents need optimization!")
        return
    
    print(f"🚀 Auto-optimizing {len(candidates)} agents...")
    
    for candidate in candidates:
        agent_name = candidate["agent_name"]
        print(f"\n🔧 Optimizing {agent_name}...")
        
        try:
            await optimize_agent(agent_name, auto=True)
        except Exception as e:
            print(f"❌ Failed to optimize {agent_name}: {e}")
    
    print(f"\n🎉 Auto-optimization complete!")

def main():
    parser = argparse.ArgumentParser(description="Simple Prompt Optimization CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Performance command
    subparsers.add_parser("performance", help="Show performance summary for all agents")
    
    # Candidates command
    subparsers.add_parser("candidates", help="List agents that need optimization")
    
    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Optimize a specific agent")
    optimize_parser.add_argument("agent", help="Agent name to optimize")
    
    # Auto-optimize command
    subparsers.add_parser("auto", help="Automatically optimize all candidates")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "performance":
        list_performance()
    elif args.command == "candidates":
        list_candidates()
    elif args.command == "optimize":
        asyncio.run(optimize_agent(args.agent))
    elif args.command == "auto":
        asyncio.run(auto_optimize_all())

if __name__ == "__main__":
    main()