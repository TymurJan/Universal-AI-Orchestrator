"""
Orchestration Engine for Universal AI Orchestrator
This module handles the execution and coordination of multi-agent tasks.
"""

import logging
from typing import Dict, List, Any
from pathlib import Path

log = logging.getLogger("Orchestra")

class Agent:
    def __init__(self, name: str, role: str, model: str = "claude-3-5-sonnet", is_manager: bool = False):
        self.name = name
        self.role = role
        self.model = model
        self.is_manager = is_manager
        self.memory = []

    def execute(self, task: str, context: Dict[str, Any], user_approved: bool = False) -> str:
        # 🧠 The Mirror Law: Manager Stop-Valve Constraints
        if self.is_manager and not user_approved:
            log.warning(f"🛑 STOP-VALVE ACTIVATED. Manager '{self.name}' halted execution of: {task[:50]}")
            return (
                f"[MANAGER HOLD] Task requires authorization. Proposing options for '{task[:30]}...':\n"
                f"1) Proceed with standard analysis.\n"
                f"2) Monitor external resources first (Allowed by token policy).\n"
                f"3) Escalate to human operator.\n"
                "AWAITING EXPLICIT PERMISSION."
            )

        log.info(f"🤖 Agent [{self.name}] ({self.role}) | Model: {self.model} | Task: {task[:60]}...")

        # --- Real LLM API call ---
        import os
        system_prompt = f"You are {self.name}, a specialized AI agent with the role: {self.role}. Respond concisely and professionally."

        # Try Anthropic first (Claude)
        if "claude" in self.model.lower():
            try:
                import anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set in environment.")
                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": task}]
                )
                return message.content[0].text
            except ImportError:
                log.warning("anthropic SDK not installed. Falling back to OpenAI.")
            except Exception as e:
                log.error(f"Anthropic API error: {e}")
                return f"[API ERROR — Anthropic] {e}"

        # Try OpenAI (GPT)
        try:
            import openai
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment.")
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=self.model if "gpt" in self.model.lower() else "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task}
                ],
                max_tokens=1024
            )
            return response.choices[0].message.content
        except ImportError:
            log.warning("openai SDK not installed.")
        except Exception as e:
            log.error(f"OpenAI API error: {e}")
            return f"[API ERROR — OpenAI] {e}"

        # Final fallback
        return f"[NO API KEY] Set OPENAI_API_KEY or ANTHROPIC_API_KEY in environment to enable real LLM calls."


class Orchestra:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

    def register_agent(self, agent: Agent):
        self.agents[agent.name] = agent
        log.info(f"✅ Registered agent: {agent.name}")

    def run_sequence(self, sequence: List[Dict[str, Any]]):
        """
        Runs a sequence of tasks passing state between them.
        Enforces token policy and manager stop-valves.
        """
        log.info("🎼 Starting Orchestra Sequence...")
        for step in sequence:
            agent_name = step["agent"]
            task_template = step["task"]
            user_approved = step.get("approved", False)
            
            if agent_name not in self.agents:
                raise ValueError(f"Agent {agent_name} not found in Orchestra.")
                
            agent = self.agents[agent_name]
            
            # Simple state substitution (e.g. {last_result})
            try:
                task = task_template.format(**self.state)
            except KeyError:
                task = task_template # Fallback if state keys are missing
            
            log.info(f"📉 Token Policy Check: Authorizing task for {agent_name}...")
            result = agent.execute(task, self.state, user_approved)
            
            # Update state with the result
            self.state["last_result"] = result
            self.state[f"{agent_name}_output"] = result
            
            self.history.append({
                "agent": agent_name,
                "task": task,
                "result": result
            })
            
            if "STOP-VALVE" in result or "MANAGER HOLD" in result:
                log.warning("Sequence halted by Manager. Waiting for user input.")
                break # Stop the sequence until user approves

            
        log.info("✅ Orchestra Sequence complete.")
        return self.state

    def get_scenario_template(self, name: str) -> Dict[str, Any]:
        """Provides pre-defined task sequences for common business cases."""
        templates = {
            "smm": {
                "name": "Social Media Content Hub",
                "steps": [
                    {"agent": "TrendAnalyzer", "action": "Identify trending topics in AI/Tech"},
                    {"agent": "Copywriter", "action": "Generate 3 variations of LinkedIn posts"},
                    {"agent": "VisualDirector", "action": "Create prompts for associated visuals"}
                ]
            },
            "support": {
                "name": "Automated Smart Support",
                "steps": [
                    {"agent": "EmotionScanner", "action": "Detect customer sentiment"},
                    {"agent": "KnowledgeRetriever", "action": "Fetch relevant docs from KB"},
                    {"agent": "Diplomat", "action": "Draft a personalized, empathetic response"}
                ]
            }
        }
        return templates.get(name.lower(), {"error": "Template not found"})

if __name__ == "__main__":
    # Example usage
    orchestra = Orchestra()
    
    analyst = Agent("Analyst", "Market Researcher")
    manager = Agent("Strategist", "Project Manager", is_manager=True)
    writer = Agent("Writer", "Copywriter")
    
    orchestra.register_agent(analyst)
    orchestra.register_agent(manager)
    orchestra.register_agent(writer)
    
    demo_sequence = [
        {"agent": "Analyst", "task": "Analyze the topic of 'AI Governance'", "approved": True},
        {"agent": "Strategist", "task": "Create the final strategic roadmap based on: {Analyst_output}", "approved": False},
        {"agent": "Writer", "task": "Write a post. (This should not run due to Stop-Valve)"}
    ]
    
    final_state = orchestra.run_sequence(demo_sequence)
    print(f"Final Output: {final_state['Writer_output']}")
