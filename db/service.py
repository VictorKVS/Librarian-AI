# 📄 db/service.py

import os
import json
from typing import List, Dict

from .storage import session_scope, SessionModel, EntityModel, SessionEntity


def get_session_entities(session_id: str) -> List[Dict]:
    """
    Возвращает все сущности, связанные с заданной сессией.
    """
    with session_scope() as db:
        rows = (
            db.query(EntityModel)
              .join(SessionEntity, EntityModel.id == SessionEntity.entity_id)
              .filter(SessionEntity.session_id == session_id)
              .order_by(EntityModel.confidence.desc())
              .all()
        )
        return [
            {
                "id": e.id,
                "type": e.entity_type,
                "value": e.text,
                "confidence": e.confidence,
                "context": e.context
            }
            for e in rows
        ]


def get_knowledge_graph(session_id: str) -> Dict:
    """
    Загружает граф знаний, связанный с сессией, из JSON-файла.
    """
    with session_scope() as db:
        sess = db.query(SessionModel).get(session_id)
        if sess and sess.graph_path and os.path.exists(sess.graph_path):
            with open(sess.graph_path, encoding="utf-8") as f:
                return json.load(f)
    return {"nodes": [], "edges": []}
