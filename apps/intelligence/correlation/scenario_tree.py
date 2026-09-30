from pydantic import BaseModel
from apps.intelligence.correlation.situation import Situation, CAUSAL_TRANSITIONS
from apps.intelligence.correlation.dna import IncidentDNA

class ScenarioNode(BaseModel):
    concept: str
    probability: float
    evidence: list[str]
    children: list['ScenarioNode'] = []
    provenance: str = 'forecast'  # observed, corroborated, inferred, forecast

class ScenarioTree(BaseModel):
    situation_id: str
    root_concepts: list[str]
    branches: list[ScenarioNode]
    total_scenarios: int
    generated_at: str  # ISO timestamp

def generate_scenario_tree(situation: Situation, max_depth: int = 3, min_probability: float = 0.1) -> ScenarioTree:
    """
    Generate a tree of alternative future scenarios branching from
    the current situation state. Each path through the tree represents
    one possible future trajectory.
    
    Uses the causal knowledge base to project what developments could follow,
    creating branching paths where multiple outcomes are possible.
    """
    # Get active concepts from the latest incident
    latest_incident = sorted(situation.incidents, key=lambda i: i.start_time)[-1]
    active_concepts = set()
    for inc in situation.incidents:
        for c in inc.core_concepts:
            active_concepts.add(c.concept)
    
    root_concepts = [c.concept for c in latest_incident.core_concepts[:3]]
    
    def build_branches(parent_concepts: set, depth: int, visited: set) -> list[ScenarioNode]:
        if depth <= 0:
            return []
        
        branches = []
        for concept in parent_concepts:
            for (cause, effect), score in CAUSAL_TRANSITIONS.items():
                if cause == concept and effect not in visited and effect not in active_concepts:
                    # Calculate weighted probability
                    prob = score * 0.8  # Decay factor for uncertainty
                    if prob < min_probability:
                        continue
                    
                    new_visited = visited | {effect}
                    children = build_branches({effect}, depth - 1, new_visited)
                    
                    node = ScenarioNode(
                        concept=effect,
                        probability=round(prob, 4),
                        evidence=[f"Causal transition from '{cause}' (strength={score:.2f})"],
                        children=children,
                        provenance='forecast',
                    )
                    branches.append(node)
        
        # Sort by probability descending
        branches.sort(key=lambda b: b.probability, reverse=True)
        return branches
    
    branches = build_branches(set(root_concepts), max_depth, set(root_concepts) | active_concepts)
    
    # Count total scenarios (leaf nodes)
    def count_leaves(nodes: list[ScenarioNode]) -> int:
        if not nodes:
            return 0
        total = 0
        for node in nodes:
            if not node.children:
                total += 1
            else:
                total += count_leaves(node.children)
        return total
    
    from datetime import datetime, timezone
    return ScenarioTree(
        situation_id=situation.situation_id,
        root_concepts=root_concepts,
        branches=branches,
        total_scenarios=max(count_leaves(branches), len(branches)),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
