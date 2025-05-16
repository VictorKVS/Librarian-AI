# 📄 Файл: graph_tools.py
# 📂 Путь установки: librarian_ai/core/graph_tools.py

 """6. Интеллектуальный анализ графа:
detect_communities(graph): определение сообществ (кластеризация) с помощью алгоритмов Louvain, Girvan-Newman и др.

rank_entities(graph, method='pagerank'): оценка важности узлов с использованием PageRank, Centrality.

🌐 7. Географическая интеграция:
geo_enrich(graph): добавление координат к LOCATION-сущностям (через GeoNames, Nominatim).

export_geojson(graph): экспорт графа с координатами в формат GeoJSON.

📊 8. Интеграция с аналитикой:
graph_to_dataframe(graph): преобразование в pandas.DataFrame для аналитических задач.

generate_html_report(graph): отчёт по графу (HTML+JS визуализация + таблицы).

generate_pdf_summary(graph): формирование PDF-отчета с инфографикой и описанием сущностей.

🧠 9. Интеграция с LLM:
explain_entity_links(graph, model): генерация объяснений связей между сущностями.

suggest_graph_edits(graph, model): предложения по очистке/обогащению графа.

🌐 10. Web-визуализация и API:
serve_graph_dashboard(graph): интерактивный интерфейс на основе Dash/Streamlit.

REST API (FastAPI): загрузка сущностей → генерация графа → визуализация и экспорт.

💡 Что выбрать следующим?
Вы можете выбрать один из следующих вариантов, и я реализую его:

 detect_communities(graph) — кластеризация узлов

 rank_entities(graph) — важность сущностей

 graph_to_dataframe(graph) — в Pandas

 export_geojson(graph) — карты

 generate_html_report(graph) — отчёт с визуализацией

 serve_graph_dashboard(graph) — web-интерфейс"""""





import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict, Optional
from entity_extractor import Entity
from collections import defaultdict

def build_entity_graph(entities: List[Entity]) -> nx.Graph:
    """
    Строит граф связей между сущностями на основе их контекста
    
    :param entities: Список извлеченных сущностей
    :return: Граф NetworkX с сущностями и связями
    """
    G = nx.Graph()
    
    # Добавляем узлы с атрибутами
    for i, entity in enumerate(entities):
        G.add_node(
            entity.text,
            label=entity.label,
            value=entity.value,
            confidence=entity.confidence
        )
    
    # Строим связи на основе общего контекста
    context_map = defaultdict(list)
    for entity in entities:
        if entity.context:
            context_map[entity.context].append(entity.text)
    
    for context, entity_texts in context_map.items():
        for i in range(len(entity_texts)):
            for j in range(i+1, len(entity_texts)):
                G.add_edge(
                    entity_texts[i], 
                    entity_texts[j],
                    context=context,
                    weight=1.0  # Можно настроить на основе confidence
                )
    
    return G

def trace_entity_paths(
    graph: nx.Graph, 
    source: str, 
    target: str,
    algorithm: str = 'dijkstra'
) -> List[str]:
    """
    Находит кратчайший путь между двумя сущностями в графе
    
    :param graph: Граф сущностей
    :param source: Исходная сущность
    :param target: Целевая сущность
    :param algorithm: Алгоритм поиска пути ('dijkstra', 'astar', 'bellman-ford')
    :return: Список сущностей, представляющих кратчайший путь
    """
    if source not in graph or target not in graph:
        return []
    
    try:
        if algorithm == 'dijkstra':
            return nx.shortest_path(graph, source=source, target=target, weight='weight')
        elif algorithm == 'astar':
            return nx.astar_path(graph, source=source, target=target, weight='weight')
        elif algorithm == 'bellman-ford':
            return nx.bellman_ford_path(graph, source=source, target=target, weight='weight')
        else:
            return nx.shortest_path(graph, source=source, target=target)
    except nx.NetworkXNoPath:
        return []

def visualize_path(
    graph: nx.Graph,
    path: List[str],
    title: str = "Entity Path Visualization",
    filename: Optional[str] = None
):
    """
    Визуализирует найденный путь между сущностями
    
    :param graph: Исходный граф
    :param path: Список узлов пути
    :param title: Заголовок графика
    :param filename: Если указан, сохраняет в файл
    """
    plt.figure(figsize=(12, 8))
    
    # Позиционирование узлов
    pos = nx.spring_layout(graph, seed=42)
    
    # Отрисовка всего графа
    nx.draw_networkx_nodes(graph, pos, node_size=300, node_color='lightblue')
    nx.draw_networkx_edges(graph, pos, alpha=0.2)
    nx.draw_networkx_labels(graph, pos, font_size=8)
    
    # Выделение пути
    if len(path) > 1:
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_nodes(graph, pos, nodelist=path, node_size=500, node_color='red')
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=2, edge_color='red')
    
    plt.title(title)
    plt.axis('off')
    
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close()
    else:
        plt.show()

def find_all_paths(
    graph: nx.Graph,
    source: str,
    target: str,
    cutoff: Optional[int] = None
) -> List[List[str]]:
    """
    Находит все возможные пути между двумя сущностями
    
    :param graph: Граф сущностей
    :param source: Исходная сущность
    :param target: Целевая сущность
    :param cutoff: Максимальная длина пути
    :return: Список всех возможных путей
    """
    if source not in graph or target not in graph:
        return []
    
    try:
        return list(nx.all_simple_paths(graph, source=source, target=target, cutoff=cutoff))
    except nx.NetworkXNoPath:
        return []

def calculate_path_strength(graph: nx.Graph, path: List[str]) -> float:
    """
    Вычисляет силу пути на основе весов ребер
    
    :param graph: Граф сущностей
    :param path: Список узлов пути
    :return: Общая сила пути (сумма весов)
    """
    if len(path) < 2:
        return 0.0
    
    total_strength = 0.0
    for i in range(len(path)-1):
        edge_data = graph.get_edge_data(path[i], path[i+1])
        total_strength += edge_data.get('weight', 1.0)
    
    return total_strength / (len(path)-1)

def get_entity_connections(graph: nx.Graph, entity: str, depth: int = 1) -> Dict[str, List[str]]:
    """
    Возвращает все связи сущности до указанной глубины
    
    :param graph: Граф сущностей
    :param entity: Исходная сущность
    :param depth: Глубина поиска связей
    :return: Словарь {уровень: [сущности]}
    """
    if entity not in graph:
        return {}
    
    connections = defaultdict(list)
    visited = set()
    queue = [(entity, 0)]
    
    while queue:
        current_entity, current_depth = queue.pop(0)
        
        if current_depth > depth:
            continue
            
        if current_entity in visited:
            continue
            
        visited.add(current_entity)
        connections[current_depth].append(current_entity)
        
        for neighbor in graph.neighbors(current_entity):
            if neighbor not in visited:
                queue.append((neighbor, current_depth + 1))
    
    return dict(connections)