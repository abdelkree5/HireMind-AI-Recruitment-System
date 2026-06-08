import json
import re
import logging
from typing import Any, Dict, List
from ai_engine.agents.base import AgentMessage, BaseAgent
from ai_engine.tools.registry import tool_registry

logger = logging.getLogger(__name__)

# Basic system prompt for ReAct
SYSTEM_PROMPT = """You are HireMind's Recruiter Copilot, an AI assistant for recruiters.
You have access to the following tools:
{tools}

To answer the user's request, use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (must be valid JSON)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Answer: the final answer to the original input question

Always provide valid JSON in "Action Input:".
"""

class RecruiterCopilotAgent(BaseAgent):
    """
    Conversational Copilot that uses the ReAct pattern to reason and call tools.
    """
    
    def __init__(self, llm_client=None):
        super().__init__(name="recruiter_copilot")
        self.llm_client = llm_client
        self.max_steps = 5

    def get_tool_descriptions(self) -> str:
        tools = tool_registry.list_tools(role="recruiter")
        desc = []
        for t in tools:
            # Only include copilot tools
            if "copilot" in t.get("tags", []):
                schema_str = json.dumps(t.get("input_schema", {}))
                desc.append(f"{t['name']}: {t['description']} | Input Schema: {schema_str}")
        return "\n".join(desc)

    def get_tool_names(self) -> list[str]:
        tools = tool_registry.list_tools(role="recruiter")
        return [t["name"] for t in tools if "copilot" in t.get("tags", [])]

    def _call_llm(self, prompt: str) -> str:
        """
        Calls the LLM. In a real environment, this uses transformers or OpenAI API.
        Here we mock the response or use the configured client if available.
        """
        # If no LLM configured, we do a basic keyword-based dummy routing for the sake of the MVP
        # In production, this would be: return self.llm_client.generate(prompt)
        
        # Simple heuristic logic to simulate an LLM taking an Action based on user query
        query = prompt.split("Question: ")[-1].split("\n")[0].lower()
        
        if "search" in query or "find" in query:
            return 'Thought: I need to search for candidates.\nAction: search_candidates\nAction Input: {"query": "'+query+'", "limit": 5}'
        elif "expand" in query or "related to" in query:
            return 'Thought: I need to check the skill graph.\nAction: skill_graph_expand\nAction Input: {"skill_name": "'+query.replace("expand", "").strip()+'"}'
        elif "analyze job" in query:
            return 'Thought: I need to analyze this job.\nAction: job_analysis\nAction Input: {"title": "Engineer", "description": "'+query+'"}'
        elif "generate question" in query or "interview" in query:
            return 'Thought: I need to generate an interview question.\nAction: interview_question_generate\nAction Input: {"candidate_name": "Candidate", "skills": ["python"], "job_title": "Engineer"}'
        elif "summarize" in query:
            return 'Thought: I need to summarize the CV.\nAction: candidate_summary\nAction Input: {"cv_text": "'+query+'"}'
        elif "remember" in query or "preference" in query or "past" in query:
            return 'Thought: I need to check recruiter memory.\nAction: recruiter_memory_retrieve\nAction Input: {"query": "'+query+'", "recruiter_id": "default"}'
        
        return "Thought: I now know the final answer\nAnswer: I'm not sure how to help with that."

    def _call_llm_with_observation(self, prompt: str, observation: str) -> str:
        """Simulate LLM concluding after an observation."""
        return f"Thought: I now know the final answer\nAnswer: Here are the results based on the observation: {observation}"

    def chat(self, message: str, session_id: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Executes the ReAct loop for a conversational message.
        """
        tools_str = self.get_tool_descriptions()
        tool_names = self.get_tool_names()
        
        prompt = SYSTEM_PROMPT.format(tools=tools_str, tool_names=", ".join(tool_names))
        prompt += f"\nQuestion: {message}\n"
        
        tools_used = []
        citations = []
        reasoning_summary = []
        
        current_prompt = prompt
        
        for step in range(self.max_steps):
            if step == 0:
                response = self._call_llm(current_prompt)
            else:
                response = self._call_llm_with_observation(current_prompt, observation_str)
                
            current_prompt += response + "\n"
            
            # Parse Thought
            thought_match = re.search(r"Thought: (.*?)\n", response)
            if thought_match:
                reasoning_summary.append(thought_match.group(1))
            
            # Parse Action
            action_match = re.search(r"Action: (.*?)\n", response)
            action_input_match = re.search(r"Action Input: (.*?)(?:\n|$)", response, re.DOTALL)
            answer_match = re.search(r"Answer: (.*?)(?:\n|$)", response, re.DOTALL)
            
            if answer_match:
                return {
                    "answer": answer_match.group(1).strip(),
                    "reasoning_summary": " -> ".join(reasoning_summary),
                    "tools_used": tools_used,
                    "citations": citations
                }
                
            if action_match and action_input_match:
                action = action_match.group(1).strip()
                action_input_str = action_input_match.group(1).strip()
                
                try:
                    action_input = json.loads(action_input_str)
                except json.JSONDecodeError:
                    action_input = {"raw": action_input_str}
                
                # Execute Tool
                try:
                    res = tool_registry.execute_tool(action, action_input, caller_agent="copilot", caller_role="recruiter")
                    observation = res.get("result", {})
                    tools_used.append(action)
                except Exception as e:
                    observation = {"error": str(e)}
                
                observation_str = json.dumps(observation)
                current_prompt += f"Observation: {observation_str}\n"
            else:
                # If no Action and no Answer, break to avoid infinite loop
                break

        return {
            "answer": "I reached the maximum number of reasoning steps without a final answer.",
            "reasoning_summary": " -> ".join(reasoning_summary),
            "tools_used": tools_used,
            "citations": citations
        }

    def run(self, message: AgentMessage) -> AgentMessage:
        """BaseAgent interface"""
        payload = message.payload
        user_msg = payload.get("message", "")
        session_id = payload.get("session_id", "default")
        
        result = self.chat(user_msg, session_id)
        return self.reply(message, result)

copilot_agent = RecruiterCopilotAgent()
