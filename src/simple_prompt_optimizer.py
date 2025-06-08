import asyncio
import json
import toml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from agents import Agent, ModelSettings, Runner

@dataclass
class OptimizationRequest:
    """Simple request for prompt optimization"""
    agent_name: str
    target_sessions: List[str]  # Session IDs to analyze
    optimization_goals: List[str]  # Specific goals
    notes: str = ""

class SimplePromptOptimizer:
    """Simplified prompt optimizer that works with git-versioned TOML files"""
    
    def __init__(self):
        self.chat_history_dir = Path("chat_history")
        self.etc_dir = Path("etc")
        
        # Load the prompt optimizer agent
        config = toml.load("etc/prompt_optimizer_agent.toml")
        self.optimizer_agent = Agent(
            name="Prompt Optimizer",
            instructions=config["prompt_optimizer_agent"]["instructions"],
            tools=[],
            model=config["prompt_optimizer_agent"]["model"],
            model_settings=ModelSettings(temperature=config["prompt_optimizer_agent"]["temperature"])
        )
    
    def get_current_prompt_version(self, agent_name: str) -> str:
        """Get the current version number for an agent (based on existing files)"""
        # Look for existing versioned files
        version_files = list(self.etc_dir.glob(f"{agent_name}_v*.toml"))
        if not version_files:
            return "v1"  # Current TOML is v1
        
        # Extract version numbers and find the highest
        versions = []
        for file in version_files:
            try:
                version_part = file.stem.split('_v')[1]
                versions.append(int(version_part))
            except (IndexError, ValueError):
                continue
        
        if versions:
            next_version = max(versions) + 1
            return f"v{next_version}"
        else:
            return "v2"  # Current is v1, next is v2
    
    def get_low_rated_sessions(self, agent_name: str, min_sessions: int = 3) -> List[Dict]:
        """Get sessions with low ratings for this agent"""
        if not self.chat_history_dir.exists():
            return []
        
        low_rated_sessions = []
        
        for chat_file in self.chat_history_dir.glob("*.json"):
            try:
                with open(chat_file, 'r') as f:
                    data = json.load(f)
                
                metadata = data.get("metadata", {})
                if metadata.get("agent") == agent_name:
                    rating = metadata.get("rating")
                    if rating and rating <= 2:  # Low rated (1-2 stars)
                        low_rated_sessions.append({
                            "session_id": chat_file.stem,
                            "rating": rating,
                            "notes": metadata.get("notes", ""),
                            "name": metadata.get("name", ""),
                            "messages": data.get("messages", [])
                        })
            except Exception:
                continue
        
        return low_rated_sessions[:min_sessions]  # Return up to min_sessions
    
    def get_agent_performance_summary(self, agent_name: str) -> Dict:
        """Get performance summary for an agent"""
        if not self.chat_history_dir.exists():
            return {"sessions": 0, "rated_sessions": 0, "average_rating": 0, "needs_optimization": False, "low_rated_count": 0}
        
        ratings = []
        session_count = 0
        
        for chat_file in self.chat_history_dir.glob("*.json"):
            try:
                with open(chat_file, 'r') as f:
                    data = json.load(f)
                
                metadata = data.get("metadata", {})
                if metadata.get("agent") == agent_name:
                    session_count += 1
                    rating = metadata.get("rating")
                    if rating:
                        ratings.append(rating)
            except Exception:
                continue
        
        if not ratings:
            return {"sessions": session_count, "rated_sessions": 0, "average_rating": 0, "needs_optimization": False, "low_rated_count": 0}
        
        avg_rating = sum(ratings) / len(ratings)
        needs_optimization = avg_rating < 3.5 and len(ratings) >= 3
        
        return {
            "sessions": session_count,
            "rated_sessions": len(ratings),
            "average_rating": avg_rating,
            "needs_optimization": needs_optimization,
            "low_rated_count": len([r for r in ratings if r <= 2])
        }
    
    def _format_session_for_analysis(self, session: Dict) -> str:
        """Format a session for analysis"""
        messages = session["messages"]
        
        formatted = f"""
SESSION ANALYSIS:
Rating: {session['rating']}/5
Notes: {session['notes']}
Name: {session['name']}

CONVERSATION TRANSCRIPT:
"""
        
        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            formatted += f"\n{i+1}. {role.upper()}: {content}\n"
        
        return formatted
    
    def _load_current_prompt(self, agent_name: str) -> Dict:
        """Load the current prompt configuration"""
        toml_file = self.etc_dir / f"{agent_name}.toml"
        if not toml_file.exists():
            raise ValueError(f"Agent config not found: {agent_name}")
        
        config = toml.load(toml_file)
        
        # Find the agent section
        for key, value in config.items():
            if isinstance(value, dict) and "instructions" in value:
                return {
                    "instructions": value.get("instructions", ""),
                    "model": value.get("model", "gpt-4"),
                    "temperature": value.get("temperature", 0.5),
                    "section_name": key
                }
        
        raise ValueError(f"No valid agent configuration found in {agent_name}.toml")
    
    async def optimize_prompt(self, request: OptimizationRequest) -> str:
        """Run optimization and create new versioned TOML file"""
        
        # Load current configuration
        current_config = self._load_current_prompt(request.agent_name)
        
        # Get session data
        sessions = []
        for session_id in request.target_sessions:
            chat_file = self.chat_history_dir / f"{session_id}.json"
            if chat_file.exists():
                with open(chat_file, 'r') as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    sessions.append({
                        "session_id": session_id,
                        "rating": metadata.get("rating", 1),
                        "notes": metadata.get("notes", ""),
                        "name": metadata.get("name", ""),
                        "messages": data.get("messages", [])
                    })
        
        if not sessions:
            raise ValueError("No valid sessions found for analysis")
        
        # Prepare optimization context
        session_analyses = []
        for session in sessions:
            analysis = self._format_session_for_analysis(session)
            session_analyses.append(analysis)
        
        context = f"""
PROMPT OPTIMIZATION REQUEST

TARGET AGENT: {request.agent_name}
OPTIMIZATION GOALS: {', '.join(request.optimization_goals)}
REQUEST NOTES: {request.notes}

CURRENT PROMPT CONFIGURATION:
Model: {current_config['model']}
Temperature: {current_config['temperature']}

CURRENT INSTRUCTIONS:
{current_config['instructions']}

DETAILED SESSION ANALYSES:
{'=' * 50}
"""
        
        for i, analysis in enumerate(session_analyses, 1):
            context += f"\nSESSION {i}:\n{analysis}\n{'=' * 50}\n"
        
        context += f"""

OPTIMIZATION TASK:
Based on the above sessions and feedback, generate an optimized version of the agent's instructions. 
Focus on addressing the issues identified in the low-rated sessions.

Goals: {', '.join(request.optimization_goals)}

Provide your response in the specified format with an optimization summary and the complete optimized instructions.
"""
        
        # Run the optimizer agent
        result = await Runner.run(
            self.optimizer_agent,
            input=context,
            context={}
        )
        
        optimization_result = result.final_output
        
        # Extract optimized instructions
        optimized_instructions = self._extract_optimized_instructions(optimization_result)
        
        # Create new versioned TOML file
        new_version = self.get_current_prompt_version(request.agent_name)
        new_filename = f"{request.agent_name}_{new_version}.toml"
        new_file_path = self.etc_dir / new_filename
        
        # Create the new TOML config
        new_config = {
            current_config['section_name']: {
                "instructions": optimized_instructions,
                "model": current_config['model'],
                "temperature": current_config['temperature']
            },
            "optimization_metadata": {
                "created_at": datetime.now().isoformat(),
                "parent_version": "v1" if new_version == "v2" else f"v{int(new_version[1:]) - 1}",
                "optimization_goals": request.optimization_goals,
                "analyzed_sessions": request.target_sessions,
                "optimizer_response": optimization_result[:500] + "..." if len(optimization_result) > 500 else optimization_result
            }
        }
        
        # Save the new version
        with open(new_file_path, 'w') as f:
            toml.dump(new_config, f)
        
        return new_file_path.name
    
    def _extract_optimized_instructions(self, optimizer_response: str) -> str:
        """Extract optimized instructions from the optimizer's response"""
        lines = optimizer_response.split('\n')
        
        in_instructions = False
        instructions_lines = []
        
        for line in lines:
            if "OPTIMIZED INSTRUCTIONS:" in line:
                in_instructions = True
                continue
            
            if in_instructions:
                if line.strip().startswith("```") and instructions_lines:
                    break
                instructions_lines.append(line)
        
        instructions = '\n'.join(instructions_lines).strip()
        
        # Clean up markdown
        if instructions.startswith("```"):
            instructions = instructions.split('\n', 1)[1]
        if instructions.endswith("```"):
            instructions = instructions.rsplit('\n', 1)[0]
        
        return instructions.strip()
    
    def list_optimization_candidates(self) -> List[Dict]:
        """List agents that could benefit from optimization"""
        candidates = []
        
        # Get all agent configs
        for toml_file in self.etc_dir.glob("*.toml"):
            if toml_file.name in ["config.toml", "prompt_optimizer_agent.toml"]:
                continue
            
            agent_name = toml_file.stem
            performance = self.get_agent_performance_summary(agent_name)
            
            if performance["needs_optimization"]:
                low_rated_sessions = self.get_low_rated_sessions(agent_name)
                
                candidates.append({
                    "agent_name": agent_name,
                    "performance": performance,
                    "low_rated_sessions": [s["session_id"] for s in low_rated_sessions],
                    "suggested_goals": self._suggest_optimization_goals(low_rated_sessions)
                })
        
        return candidates
    
    def _suggest_optimization_goals(self, sessions: List[Dict]) -> List[str]:
        """Suggest optimization goals based on session feedback"""
        # Analyze notes for common themes
        all_notes = " ".join([s.get("notes", "") for s in sessions]).lower()
        
        goals = []
        
        if any(word in all_notes for word in ["tool", "function", "call"]):
            goals.append("improve tool usage efficiency")
        
        if any(word in all_notes for word in ["incomplete", "unfinished", "didn't complete"]):
            goals.append("improve task completion")
        
        if any(word in all_notes for word in ["unclear", "confusing", "hard to understand"]):
            goals.append("improve response clarity")
        
        if any(word in all_notes for word in ["brand", "style", "tone"]):
            goals.append("better brand alignment")
        
        if any(word in all_notes for word in ["format", "structure", "organization"]):
            goals.append("improve output formatting")
        
        # Default goals if none detected
        if not goals:
            goals = ["improve task completion", "improve response clarity"]
        
        return goals[:3]  # Max 3 goals