import networkx as nx

class SkillKnowledgeGraph:
    """
    Ontological semantic graph that maps relationships between skills, frameworks, 
    and concepts to provide expanded vocabulary for candidate matching.
    """
    def __init__(self) -> None:
        self.graph = nx.Graph()
        self._build_initial_ontology()
        
    def _build_initial_ontology(self) -> None:
        # Edges represent "is related to", "is a sub-skill of", or "is commonly used with"
        relationships = [
            ("Python", "FastAPI"),
            ("Python", "Django"),
            ("Python", "Flask"),
            ("Python", "Machine Learning"),
            ("Python", "Data Science"),
            ("FastAPI", "REST API"),
            ("Django", "REST API"),
            ("Flask", "REST API"),
            ("JavaScript", "React"),
            ("JavaScript", "TypeScript"),
            ("JavaScript", "Node.js"),
            ("TypeScript", "React"),
            ("TypeScript", "Node.js"),
            ("React", "Redux"),
            ("React", "Frontend"),
            ("HTML", "CSS"),
            ("SQL", "PostgreSQL"),
            ("SQL", "MySQL"),
            ("Machine Learning", "Deep Learning"),
            ("Machine Learning", "scikit-learn"),
            ("Machine Learning", "NLP"),
            ("Deep Learning", "PyTorch"),
            ("Deep Learning", "TensorFlow"),
            ("Deep Learning", "Transformers"),
            ("NLP", "Transformers"),
            ("NLP", "sentence-transformers"),
            ("NLP", "LLM"),
            ("Transformers", "LLM"),
            ("Docker", "Kubernetes"),
            ("Docker", "Containers"),
            ("Kubernetes", "Containers"),
            ("Kubernetes", "Microservices"),
            ("Docker", "Microservices"),
            ("AWS", "Cloud Architecture"),
            ("Azure", "Cloud Architecture"),
            ("GCP", "Cloud Architecture"),
            ("DevOps", "Docker"),
            ("DevOps", "Kubernetes"),
            ("DevOps", "CI/CD"),
            ("DevOps", "Jenkins"),
            ("Networking", "TCP/IP"),
            ("Networking", "Routing"),
            ("Networking", "Switching"),
            ("Networking", "WAN"),
            ("Networking", "LAN"),
            ("Network Security", "Firewall"),
            ("Network Security", "VPN"),
            ("Telecommunications", "Radio Access Network"),
            ("Telecommunications", "Fiber Optics"),
            ("Telecommunications", "Microwave"),
            ("Telecommunications", "WiMAX"),
            ("Cisco", "CCNA"),
            ("Cisco", "CCNP"),
            ("Monitoring", "Prometheus"),
            ("Monitoring", "Grafana"),
            ("Monitoring", "Splunk"),
            ("Monitoring", "ELK"),
            ("Linux", "Bash"),
        ]
        self.graph.add_edges_from(relationships)
        
    def get_expanded_skills(self, skills: list[str], max_depth: int = 1) -> set[str]:
        """
        Takes a list of extracted flat skills and expands them using the graph
        to include semantic synonyms or closely related parent/child concepts.
        """
        expanded = set(skills)
        for skill in skills:
            # Case insensitive match to find node
            node = next((n for n in self.graph.nodes() if n.lower() == skill.lower()), None)
            if node:
                # Get neighbors up to max_depth
                neighbors = set(self.graph.neighbors(node))
                expanded.update(neighbors)
                
                if max_depth > 1:
                    for neighbor in list(neighbors):
                        expanded.update(self.graph.neighbors(neighbor))
        
        return expanded

    def expand_skill(self, skill: str) -> list[str]:
        """Expands a single skill name and returns it as a list of related skill names."""
        return list(self.get_expanded_skills([skill]))

# Singleton instance
skill_graph = SkillKnowledgeGraph()
