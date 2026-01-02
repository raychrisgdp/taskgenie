# PR-014: Multi-Agent Orchestration (Spec)

**Status:** Spec Only  
**Depends on:** PR-003B, PR-013  
**Last Reviewed:** 2026-01-01

## Goal

Enable multiple agents to collaborate on a goal with shared memory and coordinated
execution.

## User Value

- Complex goals can be decomposed across specialized agents.
- Users can track agent progress and outcomes over time.

## References

- `docs/01-design/DESIGN_CHAT.md`
- `docs/01-design/DESIGN_ARCHITECTURE.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- Agent manager that spawns and supervises agent runs.
- Shared memory store for agent context and summaries.
- Run lifecycle: start, pause, resume, cancel, complete.
- Concurrency controls and rate limiting.

### Out

- Agent marketplace or third-party agent plugins.
- Cross-user collaboration and shared workspaces.

## Mini-Specs

- `AgentRun` record with status, goal, timestamps, and summary.
- `AgentManager` orchestrates runs and delegates tool calls.
- Shared memory storage for summaries and recent context.
- Event integration to emit run status updates (PR-013).

## User Stories

- As a user, I can launch an agent run and watch progress updates.
- As a user, I can pause or cancel a long-running agent.

## UX Notes (if applicable)

- Provide a clear "running" indicator and last-updated timestamp.

## Technical Design

### Architecture

- Supervisor process manages agent workers and run state.
- Agent workers execute plans using the tool-calling foundation.
- Memory store persists summaries and last-known context for runs.

### Data Model / Migrations

- `agent_runs` table: id, goal, status, started_at, finished_at, summary.
- Optional `agent_messages` table for recent context slices.

### API Contract

- `POST /api/v1/agents/run` starts a run and returns `run_id`.
- `GET /api/v1/agents/{run_id}` returns status and summary.
- `POST /api/v1/agents/{run_id}/cancel` cancels a run.

### Background Jobs

- Agent worker loop and run scheduler.

### Security / Privacy

- Run data stored locally; no prompts or responses logged by default.

### Error Handling

- Failed runs are marked with error status and short reason.

### Implementation Notes

#### Architectural Pattern Selection

Implement **Swarm/Peer-to-Peer** pattern (not Supervisor) to avoid telephone game:

```python
@dataclass
class AgentDefinition:
    """Agent definition for swarm pattern."""
    name: str
    role: str  # researcher, planner, executor
    tools: list[str]  # Tools available to this agent
    system_prompt: str | None = None  # Optional role-specific prompt
    can_handoff: bool = True  # Supports peer handoff

class SwarmOrchestrator:
    """Peer-to-peer agent orchestration without supervisor bottleneck."""

    def __init__(self):
        self.agents: dict[str, AgentDefinition] = {}
        self.active_runs: dict[str, AgentRun] = {}

    def register_agent(self, agent_def: AgentDefinition):
        """Register agent with role and tools."""
        self.agents[agent_def.name] = agent_def
        logger.info({
            "event": "agent_registered",
            "agent_name": agent_def.name,
            "role": agent_def.role,
            "tools": agent_def.tools
        })

    async def delegate_task(self, goal: str, context: dict) -> AgentRun:
        """Delegate to appropriate specialist agent."""
        # Analyze goal to select initial agent
        initial_agent = self._select_agent(goal)

        # Create run with isolated context
        run_id = str(uuid.uuid4())
        run = AgentRun(
            id=run_id,
            goal=goal,
            agent_name=initial_agent.name,
            status="running",
            started_at=datetime.now()
        )

        self.active_runs[run_id] = run

        logger.info({
            "event": "run_started",
            "run_id": run_id,
            "agent": initial_agent.name,
            "goal": goal
        })

        # Initial agent has control
        return await initial_agent.execute(run_id, goal, context, self)

    def _select_agent(self, goal: str) -> AgentDefinition:
        """Select appropriate agent based on goal analysis."""
        goal_lower = goal.lower()

        if any(kw in goal_lower for kw in ["research", "find", "search", "look up"]):
            return self.agents.get("researcher")
        elif any(kw in goal_lower for kw in ["plan", "design", "organize", "schedule"]):
            return self.agents.get("planner")
        elif any(kw in goal_lower for kw in ["execute", "do", "implement", "write", "create"]):
            return self.agents.get("executor")
        else:
            return self.agents.get("generalist")

# Example agent definitions
RESEARCHER = AgentDefinition(
    name="researcher",
    role="Research specialist",
    system_prompt="You are a research specialist. Gather information from available sources and provide factual findings.",
    tools=["search_tasks", "search_rag", "fetch_attachment"],
    can_handoff=True
)

PLANNER = AgentDefinition(
    name="planner",
    role="Planning specialist",
    system_prompt="You are a planning specialist. Break down goals into actionable steps and delegate to specialists.",
    tools=["list_tasks", "create_task", "add_attachment"],
    can_handoff=True
)

EXECUTOR = AgentDefinition(
    name="executor",
    role="Execution specialist",
    system_prompt="You are an execution specialist. Perform tasks directly using available tools. Focus on correctness and efficiency.",
    tools=["update_task", "mark_done", "delete_task"],
    can_handoff=False
)

orchestrator = SwarmOrchestrator()
orchestrator.register_agent(RESEARCHER)
orchestrator.register_agent(PLANNER)
orchestrator.register_agent(EXECUTOR)
```

#### Handoff Protocol

Implement explicit handoff mechanism with `forward_message` tool:

```python
def forward_to_agent(
    agent_name: str,
    message: str,
    context: dict | None = None
) -> dict:
    """
    Forward to another agent with full context preservation.

    Use when:
    - Current agent lacks required tools for task
    - Task requires different specialization
    - Agent reached depth/convergence limit

    Returns:
        Handoff directive with target agent and full message
    """
    return {
        "type": "handoff",
        "target_agent": agent_name,
        "message": message,
        "context": context  # Pass accumulated context
    }

# Register as tool in agent tool definitions
HANDOFF_TOOL = ToolDefinition(
    name="forward_to_agent",
    description=(
        "Transfer control to a different agent. "
        "Use when current agent lacks required tools or specialization. "
        "Preserves full conversation context for handoff."
    ),
    parameters=ToolParameter(
        name="args",
        type="object",
        required=True,
        properties={
            "agent_name": {
                "type": "string",
                "description": "Target agent name"
            },
            "message": {
                "type": "string",
                "description": "Reason for handoff and accumulated findings"
            }
        }
    )
)

# Agent usage
async def researcher_agent(goal: str, context: dict) -> dict:
    """Researcher agent with handoff capability."""
    findings = await perform_research(goal)

    # If goal requires planning, handoff to planner
    if requires_planning(goal):
        return forward_to_agent("planner", f"Research findings: {findings}", context)

    # If goal requires execution, handoff to executor
    if requires_execution(goal):
        return forward_to_agent("executor", f"Action plan: {findings}", context)

    return {"type": "final", "result": findings}
```

#### Convergence and Consensus

Implement debate protocol for complex decisions:

```python
class DebateCoordinator:
    """Coordinate debate between multiple agents."""

    def __init__(self):
        self.participants: list[str] = []
        self.round: int = 0
        self.max_rounds: int = 3

    async def coordinate(self, question: str) -> dict:
        """Run debate and aggregate results."""
        self.participants = self._select_participants(question)
        self.round = 0

        while self.round < self.max_rounds:
            self.round += 1

            # Get positions from all agents
            positions = await self._gather_positions(question)

            # Critique phase: agents critique each other's positions
            critiques = await self._gather_critiques(positions)

            # Present critiques to agents for next round
            updated_positions = await self._incorporate_critiques(positions, critiques)

            # Check convergence
            if self._has_converged(updated_positions):
                break

        return self._aggregate_results(updated_positions)

    def _select_participants(self, question: str) -> list[str]:
        """Select relevant agents for question."""
        question_lower = question.lower()

        if "github" in question_lower or "pr" in question_lower:
            return ["github_specialist", "code_reviewer"]
        elif "email" in question_lower or "gmail" in question_lower:
            return ["gmail_specialist", "email_analyst"]
        else:
            return ["generalist", "researcher", "planner"]

    def _has_converged(self, positions: list[dict]) -> bool:
        """Check if agents have converged."""
        if len(positions) < 2:
            return False

        # Check agreement threshold (e.g., 80% agree)
        positions_text = [p.get("answer") for p in positions]
        most_common = max(set(positions_text), key=positions_text.count)
        agreement_ratio = positions_text.count(most_common) / len(positions_text)

        return agreement_ratio >= 0.8

    def _aggregate_results(self, positions: list[dict]) -> dict:
        """Aggregate debate results."""
        # Weight votes by confidence
        weighted_votes = []
        for p in positions:
            confidence = p.get("confidence", 0.5)
            weighted_votes.extend([p.get("answer")] * int(confidence * 10))

        most_common = max(set(weighted_votes), key=weighted_votes.count)

        return {
            "type": "consensus",
            "answer": most_common,
            "confidence": weighted_votes.count(most_common) / len(weighted_votes),
            "rounds": self.round
        }
```

#### Failure Mode Mitigations

**Supervisor Bottleneck:** Implement output schema constraints

```python
@dataclass
class SupervisorOutput:
    """Constrained output to prevent supervisor context bloat."""
    status: str  # "success", "partial", "failed"
    summary: str  # Concise summary only
    findings: list[str]  # Key findings (not full context)
    next_actions: list[str]  # Actionable next steps

def supervisor_delegate(
    task: str,
    sub_agents: list[str]
) -> SupervisorOutput:
    """Delegate to sub-agents with constrained output."""
    results = await asyncio.gather([
        run_agent(agent, task) for agent in sub_agents
    ])

    return SupervisorOutput(
        status="success",
        summary=f"Delegated to {len(results)} agents",
        findings=[r["output"] for r in results if "output" in r],
        next_actions=["Review findings for action plan"]
    )
```

**Divergence Prevention:** Define clear objective boundaries

```python
@dataclass
class AgentObjective:
    """Agent objective with boundaries."""
    primary_goal: str
    success_criteria: list[str]  # When to consider complete
    constraints: list[str]  # What NOT to do
    handoff_triggers: list[str]  # When to transfer control

def enforce_objectives(agent_run: AgentRun, objective: AgentObjective):
    """Enforce objective boundaries during execution."""
    current_goal = agent_run.goal.lower()

    # Check for divergence
    for constraint in objective.constraints:
        if constraint.lower() in current_goal:
            logger.warning({
                "event": "agent_divergence",
                "agent": agent_run.agent_name,
                "objective": objective.primary_goal,
                "constraint": constraint,
                "goal": agent_run.goal
            })
            return False

        return True

---

### Memory Implementation Notes

#### Shared Memory Architecture

Implement hierarchical memory with temporal validity for multi-agent coordination:

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List

@dataclass
class MemoryFact:
    """Memory fact with temporal validity."""
    entity_type: str  # "task", "attachment", "github_pr", "email"
    entity_id: str
    property_name: str
    property_value: str
    source_agent: str  # Which agent learned this fact
    valid_from: datetime  # Fact becomes valid at
    valid_until: Optional[datetime] = None  # Fact expires at
    confidence: float = 1.0  # Confidence in fact
    created_at: datetime

@dataclass
class SharedMemory:
    """Shared memory store for agent coordination."""

    def __init__(self):
        self.facts: Dict[str, MemoryFact] = {}
        self.entity_indices: Dict[str, set[str]] = {}
        self.temporal_indexes: Dict[str, list[str]] = {}

    def store_fact(
        self,
        entity_type: str,
        entity_id: str,
        property_name: str,
        property_value: str,
        source_agent: str,
        confidence: float = 1.0,
        valid_hours: int | None = None
    ) -> None:
        """Store a memory fact with optional temporal validity."""
        fact_id = f"{entity_type}:{entity_id}:{property_name}"

        valid_from = datetime.now()
        valid_until = datetime.now() + timedelta(hours=valid_hours) if valid_hours else None

        fact = MemoryFact(
            entity_type=entity_type,
            entity_id=entity_id,
            property_name=property_name,
            property_value=property_value,
            source_agent=source_agent,
            valid_from=valid_from,
            valid_until=valid_until,
            confidence=confidence,
            created_at=datetime.now()
        )

        self.facts[fact_id] = fact

        # Update entity index
        if entity_type not in self.entity_indices:
            self.entity_indices[entity_type] = set()
        self.entity_indices[entity_type].add(entity_id)

        # Update temporal index
        if valid_until:
            time_key = valid_until.strftime("%Y-%m-%d")
            if time_key not in self.temporal_indexes:
                self.temporal_indexes[time_key] = []
            self.temporal_indexes[time_key].append(fact_id)

        logger.info({
            "event": "memory_fact_stored",
            "fact_id": fact_id,
            "source_agent": source_agent,
            "confidence": confidence
        })

    def retrieve_facts(
        self,
        entity_type: str,
        entity_id: str,
        as_of: datetime | None = None
    ) -> List[MemoryFact]:
        """Retrieve facts for entity, respecting temporal validity."""
        as_of = as_of or datetime.now()
        prefix = f"{entity_type}:{entity_id}:"

        matching = [
            fact for fact_id, fact in self.facts.items()
            if fact_id.startswith(prefix)
            and fact.valid_from <= as_of
            and (fact.valid_until is None or fact.valid_until > as_of)
        ]

        # Sort by confidence and recency
        matching.sort(key=lambda f: (f.confidence, f.created_at), reverse=True)

        logger.debug({
            "event": "memory_retrieval",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "facts_found": len(matching),
            "as_of": as_of.isoformat()
        })

        return matching

    def temporal_query(
        self,
        entity_type: str,
        query_time: datetime,
        time_window_hours: int = 24
    ) -> List[MemoryFact]:
        """Query memory state as of specific time (time-travel)."""
        window_start = query_time - timedelta(hours=time_window_hours)
        window_end = query_time + timedelta(hours=time_window_hours)

        matching = [
            fact for fact in self.facts.values()
            if fact.entity_type == entity_type
            and fact.valid_from <= window_end
            and (fact.valid_until is None or fact.valid_until > window_start)
        ]

        logger.info({
            "event": "memory_temporal_query",
            "entity_type": entity_type,
            "query_time": query_time.isoformat(),
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "facts_found": len(matching)
        })

        return matching

# Global shared memory instance
shared_memory = SharedMemory()

# Agent usage
async def researcher_agent(goal: str, context: dict) -> dict:
    """Researcher agent stores findings in shared memory."""
    findings = await perform_research(goal)

    # Store in shared memory for other agents
    for finding in findings:
        shared_memory.store_fact(
            entity_type="research_finding",
            entity_id=str(hash(finding)),
            property_name="content",
            property_value=str(finding),
            source_agent="researcher",
            confidence=0.8,
            valid_hours=48  # Facts valid for 48 hours
        )

    return {"type": "final", "result": findings}

async def executor_agent(goal: str, context: dict) -> dict:
    """Executor agent reads from shared memory."""
    task_id = context.get("task_id")

    # Retrieve relevant facts about task
    task_facts = shared_memory.retrieve_facts(
        entity_type="task",
        entity_id=task_id
    )

    return {"type": "final", "result": f"Executing task with: {task_facts}"}
```

#### Entity Consistency Tracking

Track entity identity across sessions and agents:

```python
class EntityRegistry:
    """Maintain entity consistency across sessions."""

    def __init__(self, shared_memory: SharedMemory):
        self.memory = shared_memory
        self.entity_references: Dict[str, set[str]] = {}

    def track_reference(
        self,
        session_id: str,
        entity_type: str,
        entity_id: str,
        reference_text: str
    ) -> None:
        """Track when an entity is referenced in conversation."""
        key = f"{session_id}:{entity_type}"

        if key not in self.entity_references:
            self.entity_references[key] = set()

        self.entity_references[key].add(entity_id)

        # Check if this is a new entity reference
        existing_facts = self.memory.retrieve_facts(entity_type, entity_id)
        is_new_entity = len(existing_facts) == 0

        if is_new_entity:
            logger.info({
                "event": "entity_first_mention",
                "session_id": session_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "reference": reference_text[:100]
            })

    def resolve_identity(
        self,
        session_id: str,
        entity_type: str,
        entity_id: str,
        potential_matches: list[str]
    ) -> Optional[str]:
        """Resolve entity identity when multiple candidates exist."""
        key = f"{session_id}:{entity_type}"
        tracked_entities = self.entity_references.get(key, set())

        if not tracked_entities:
            return None

        # Find best match among tracked entities
        best_match = self._find_best_match(entity_id, potential_matches, tracked_entities)

        if best_match:
            # Link identities
            for entity in tracked_entities:
                if entity != best_match:
                    self.memory.store_fact(
                        entity_type="entity_alias",
                        entity_id=entity,
                        property_name="same_as",
                        property_value=best_match,
                        source_agent="system",
                        confidence=0.95,
                        valid_hours=None
                    )

            return best_match

        return entity_id

    def _find_best_match(
        self,
        entity_id: str,
        potential_matches: list[str],
        tracked_entities: set[str]
    ) -> Optional[str]:
        """Find best match using string similarity."""
        from difflib import SequenceMatcher

        best_match = None
        best_ratio = 0.0

        for candidate in tracked_entities:
            ratio = SequenceMatcher(None, candidate).ratio(entity_id)

            # Penalize matches that differ significantly from entity_id
            candidate_similarity = SequenceMatcher(None, entity_id).ratio(candidate)
            adjusted_ratio = ratio * (1.0 if candidate_similarity > 0.9 else 0.8)

            if adjusted_ratio > best_ratio:
                best_ratio = adjusted_ratio
                best_match = candidate

        return best_match
```

#### Memory Consolidation

Implement periodic consolidation to prevent unbounded growth:

```python
class MemoryConsolidator:
    """Consolidate memory to prevent unbounded growth."""

    def __init__(self, shared_memory: SharedMemory):
        self.memory = shared_memory
        self.last_consolidation: Optional[datetime] = None
        self.consolidation_interval_hours: int = 24

    async def consolidate_if_needed(self) -> dict:
        """Consolidate memory if interval elapsed."""
        now = datetime.now()

        if (self.last_consolidation is None or
            (now - self.last_consolidation).total_seconds() >
            self.consolidation_interval_hours * 3600):

            logger.info({"event": "memory_consolidation_started"})

            stats = await self._consolidate()

            self.last_consolidation = now

            return stats

        return {"status": "skipped", "reason": "Too recent"}

    async def _consolidate(self) -> dict:
        """Perform consolidation."""
        # 1. Remove outdated facts
        removed = await self._remove_outdated_facts()

        # 2. Merge duplicate facts
        merged = await self._merge_duplicate_facts()

        # 3. Update validity periods
        updated = await self._refresh_validity_periods()

        # 4. Remove low-confidence facts
        pruned = await self._prune_low_confidence()

        return {
            "removed_facts": removed,
            "merged_facts": merged,
            "updated_validity": updated,
            "pruned_low_confidence": pruned
        }

    async def _remove_outdated_facts(self) -> int:
        """Remove facts past validity period."""
        now = datetime.now()
        fact_ids_to_remove = []

        for fact_id, fact in self.memory.facts.items():
            if fact.valid_until and fact.valid_until < now:
                fact_ids_to_remove.append(fact_id)

        for fact_id in fact_ids_to_remove:
            del self.memory.facts[fact_id]

        logger.info({
            "event": "memory_consolidation",
            "action": "removed_outdated",
            "count": len(fact_ids_to_remove)
        })

        return len(fact_ids_to_remove)

    async def _merge_duplicate_facts(self) -> int:
        """Merge facts about same entity/property."""
        # Group facts by entity:property
        from collections import defaultdict
        property_groups = defaultdict(list)

        for fact_id, fact in self.memory.facts.items():
            key = f"{fact.entity_type}:{fact.entity_id}:{fact.property_name}"
            property_groups[key].append(fact)

        merged_count = 0
        for facts in property_groups.values():
            if len(facts) > 1:
                # Keep highest confidence, mark others as superseded
                facts.sort(key=lambda f: f.confidence, reverse=True)
                best_fact = facts[0]

                for fact in facts[1:]:
                    if fact.property_value != best_fact.property_value:
                        # Mark as superseded
                        self.memory.store_fact(
                            entity_type=fact.entity_type,
                            entity_id=fact.entity_id,
                            property_name="superseded_by",
                            property_value=best_fact.property_value,
                            source_agent="consolidation",
                            confidence=0.5,
                            valid_hours=None
                        )
                    merged_count += 1

        logger.info({
            "event": "memory_consolidation",
            "action": "merged_duplicates",
            "count": merged_count
        })

        return merged_count

    async def _prune_low_confidence(self) -> int:
        """Remove facts below confidence threshold."""
        confidence_threshold = 0.3

        fact_ids_to_remove = [
            fact_id for fact_id, fact in self.memory.facts.items()
            if fact.confidence < confidence_threshold
        ]

        for fact_id in fact_ids_to_remove:
            del self.memory.facts[fact_id]

        logger.info({
            "event": "memory_consolidation",
            "action": "pruned_low_confidence",
            "count": len(fact_ids_to_remove)
        })

        return len(fact_ids_to_remove)
```

#### Integration with Context Loading

Load relevant memories into agent context:

```python
async def load_relevant_memory(
    agent_name: str,
    goal: str,
    context_budget: int = 2000
) -> str:
    """Load relevant memories into agent context."""
    # Extract entities from goal
    entities = extract_entities(goal)

    relevant_facts = []
    tokens_used = 0

    for entity_type, entity_id in entities:
        facts = shared_memory.retrieve_facts(entity_type, entity_id)

        for fact in facts:
            fact_tokens = estimate_tokens(str(fact))

            if tokens_used + fact_tokens <= context_budget:
                relevant_facts.append(fact)
                tokens_used += fact_tokens
            else:
                break

    if not relevant_facts:
        return ""

    memory_context = "\n\n".join([
        f"[Memory from {fact.source_agent}] {fact.entity_type}:{fact.entity_id} "
        f"{fact.property_name}={fact.property_value} "
        f"(confidence: {fact.confidence})"
        for fact in relevant_facts
    ])

    logger.info({
        "event": "memory_context_loaded",
        "agent": agent_name,
        "entities_count": len(entities),
        "facts_loaded": len(relevant_facts),
        "tokens_used": tokens_used,
        "tokens_remaining": context_budget - tokens_used
    })

    return memory_context

def estimate_tokens(text: str) -> int:
    """Rough token estimation."""
    return len(text.split()) * 1.3
```

#### Agent Task Summarization

Store agent summaries in memory for future retrieval:

```python
@dataclass
class AgentRunSummary:
    """Summary of agent run stored in memory."""
    run_id: str
    agent_name: str
    goal: str
    summary: str  # Exec summary
    key_findings: list[str]  # Important discoveries
    outcomes: list[str]  # Results achieved
    tokens_used: int
    duration_seconds: int

async def store_agent_summary(
    run: AgentRun,
    summary: str,
    key_findings: list[str],
    outcomes: list[str]
) -> None:
    """Store agent run summary in shared memory."""
    run_summary = AgentRunSummary(
        run_id=run.id,
        agent_name=run.agent_name,
        goal=run.goal,
        summary=summary,
        key_findings=key_findings,
        outcomes=outcomes,
        tokens_used=run.tokens_used or 0,
        duration_seconds=(run.finished_at - run.started_at).total_seconds() if run.finished_at else 0
    )

    # Store as memory facts for later retrieval
    shared_memory.store_fact(
        entity_type="agent_run",
        entity_id=run.id,
        property_name="summary",
        property_value=summary,
        source_agent=run.agent_name,
        confidence=0.9,
        valid_hours=None
    )

    for i, finding in enumerate(key_findings):
        shared_memory.store_fact(
            entity_type="agent_run",
            entity_id=run.id,
            property_name=f"finding_{i}",
            property_value=finding,
            source_agent=run.agent_name,
            confidence=0.8,
            valid_hours=None
        )

    for i, outcome in enumerate(outcomes):
        shared_memory.store_fact(
            entity_type="agent_run",
            entity_id=run.id,
            property_name=f"outcome_{i}",
            property_value=outcome,
            source_agent=run.agent_name,
            confidence=0.9,
            valid_hours=None
        )

    logger.info({
        "event": "agent_summary_stored",
        "run_id": run.id,
        "agent": run.agent_name,
        "key_findings": len(key_findings),
        "outcomes": len(outcomes)
    })
```

## Acceptance Criteria

### AC1: Run Lifecycle

**Success Criteria:**
- [ ] Agent runs can be started, paused, resumed, and canceled.
- [ ] Run status is persisted and queryable.

### AC2: Concurrency Control

**Success Criteria:**
- [ ] Concurrency limits prevent excessive parallel runs.
- [ ] Runs back off or queue when limits are reached.

### AC3: Event Integration

**Success Criteria:**
- [ ] Run status updates emit events for UI consumption.

## Test Plan

### Automated

- Unit tests for run state transitions.
- Integration tests for API start/cancel/status.
- Concurrency tests for max-parallel settings.

### Manual

- Start a run, observe status updates, then cancel it.

## Notes / Risks / Open Questions

- Decide how much agent context to persist vs summarize.
