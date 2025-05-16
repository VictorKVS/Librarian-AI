# 📄 Файл: graph_store.py
# 📂 Путь установки: librarian_ai/graph/graph_store.py
# 📌 Назначение: управление графом знаний для GraphRAG (Neo4j)
# 📥 Получает: сущности и связи от модуля классификации/анализа (например, classifier или enricher)
# ⚙️ Делает: создаёт, связывает и хранит узлы и отношения в графовой БД
# 📤 Передаёт: результаты запросов (связанные сущности) в LLM или визуализации (через retriever или аналитику)

from neo4j import GraphDatabase
from typing import List, Dict

class GraphStore:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="test"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_entity(self, entity: str, label: str = "Concept"):
        with self.driver.session() as session:
            session.run("CREATE (e:%s {name: $name})" % label, name=entity)

    def add_relation(self, source: str, target: str, rel_type: str):
        with self.driver.session() as session:
            session.run(
                "MATCH (a {name: $source}), (b {name: $target}) "
                "MERGE (a)-[r:%s]->(b)" % rel_type,
                source=source, target=target
            )

    def query_related(self, entity: str, depth: int = 1) -> List[Dict]:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (a {name: $name})-[*1..%d]-(b) RETURN DISTINCT b.name AS name" % depth,
                name=entity
            )
            return [record.data() for record in result]

    def clear_graph(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")


if __name__ == "__main__":
    store = GraphStore()
    store.clear_graph()
    store.add_entity("Криптография")
    store.add_entity("Электронная подпись")
    store.add_relation("Криптография", "Электронная подпись", "УПРАВЛЯЕТ")
    print(store.query_related("Криптография"))
    store.close()