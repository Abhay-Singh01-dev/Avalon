from __future__ import annotations

import json
import math
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.core.logger import get_logger
from app.core.retry import retry_llm_call
from app.db.mongo import get_collection
from app.llm.lmstudio_client import lmstudio_client


class GraphBuilder:
    """Service responsible for constructing, persisting, and loading expert graphs."""

    NODE_COLORS = {
        "expert": "#3182CE",
        "institution": "#2F855A",
        "trial": "#D69E2E",
        "patent": "#B83280",
        "document": "#805AD5",
    }

    SCORE_WEIGHTS = {
        "publications": 2.5,
        "trials": 4.0,
        "patents": 3.2,
        "recent_activity": 1.5,
        "web_intel": 1.0,
    }

    def __init__(self, graph_dir: Optional[Path] = None, llm_client=lmstudio_client):
        self._logger = get_logger(__name__)
        self.graph_dir = Path(graph_dir or Path(__file__).resolve().parents[2] / "graphs")
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self.llm_client = llm_client
        self.llm_call = retry_llm_call()(self.llm_client.ask_llm)
        self.graph_collection = get_collection("expert_graphs")

    async def build_graph(self, query: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Main orchestration pipeline for graph construction."""
        signals = signals or {}
        raw_entities = self._collect_entities(signals)
        normalized_entities = await self._normalize_entities(raw_entities, query)
        entity_nodes, alias_index = self._build_entity_nodes(normalized_entities, query)

        context_nodes = {}
        self._ingest_context_nodes(context_nodes, signals)

        edges: List[Dict[str, Any]] = []
        edges += self._build_affiliation_edges(normalized_entities, context_nodes)
        edges += self._build_document_edges(normalized_entities)
        edges += self._build_trial_edges(signals, alias_index, context_nodes)
        edges += self._build_patent_edges(signals, alias_index, context_nodes)
        edges += self._build_collaboration_edges(normalized_entities)

        nodes = entity_nodes + list(context_nodes.values())

        graph_id = uuid.uuid4().hex
        meta = {
            "graph_id": graph_id,
            "query": query,
            "created_at": datetime.utcnow().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "channels": list(signals.keys()),
        }

        graph_payload = {"graph_id": graph_id, "nodes": nodes, "edges": edges, "meta": meta}
        file_path = self._save_graph_file(graph_payload)
        await self._persist_metadata(graph_id, query, meta, file_path)

        recommendations = self._build_recommendations(normalized_entities)
        preview = {
            "experts": recommendations,
            "summary": f"{len(recommendations)} prioritized experts for '{query}'",
        }

        graph_payload["meta"]["path"] = str(file_path)
        graph_payload["meta"]["recommendations"] = recommendations

        return {"graph_id": graph_id, "graph": graph_payload, "preview": preview}

    def load_graph(self, graph_id: str) -> Dict[str, Any]:
        """Load a graph file from disk."""
        graph_id = (graph_id or "").replace("graph_", "")
        file_path = self.graph_dir / f"graph_{graph_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Graph {graph_id} not found")
        with file_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    async def _normalize_entities(self, entities: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        if not entities:
            return []

        dedup: Dict[str, Dict[str, Any]] = {}
        batch_size = 5
        for i in range(0, len(entities), batch_size):
            batch = entities[i : i + batch_size]
            normalized_batch = await self._llm_normalize_batch(batch, query)

            for raw_entity, enriched in zip(batch, normalized_batch):
                canonical_name = (enriched.get("canonical_name") or raw_entity.get("raw_name") or "").strip()
                if not canonical_name:
                    continue

                affiliations = self._ensure_list(enriched.get("affiliations") or raw_entity.get("affiliations"))
                entity_type = enriched.get("type") or raw_entity.get("type") or "expert"
                fingerprint = self._make_fingerprint(canonical_name, affiliations)

                entity_id = enriched.get("id")
                if not entity_id:
                    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, fingerprint or canonical_name)
                    entity_id = f"{entity_type}:{namespace.hex}"

                contact = self._normalize_contact(enriched.get("contact"), raw_entity.get("contact"))

                record = {
                    "id": entity_id,
                    "label": canonical_name,
                    "type": entity_type,
                    "affiliations": affiliations,
                    "expertise": self._ensure_list(enriched.get("expertise") or raw_entity.get("expertise")),
                    "aliases": sorted(set(self._ensure_list(raw_entity.get("aliases")) + [raw_entity.get("raw_name")])),
                    "contact": contact,
                    "source_channels": sorted(
                        set(self._ensure_list(raw_entity.get("channels")) + self._ensure_list(enriched.get("channels")))
                    ),
                    "document_ids": set(self._ensure_list(raw_entity.get("document_ids"))),
                    "trial_ids": set(self._ensure_list(raw_entity.get("trial_ids"))),
                    "patent_ids": set(self._ensure_list(raw_entity.get("patent_ids"))),
                    "web_ids": set(self._ensure_list(raw_entity.get("web_ids"))),
                    "evidence": set(self._ensure_list(raw_entity.get("evidence"))),
                    "recent_activity": raw_entity.get("recent_activity", 0),
                }

                if fingerprint in dedup:
                    dedup[fingerprint] = self._merge_entity_records(dedup[fingerprint], record)
                else:
                    dedup[fingerprint] = record

        for entity in dedup.values():
            entity["document_ids"] = sorted(entity["document_ids"])
            entity["trial_ids"] = sorted(entity["trial_ids"])
            entity["patent_ids"] = sorted(entity["patent_ids"])
            entity["web_ids"] = sorted(entity["web_ids"])
            entity["evidence"] = sorted(entity["evidence"])

        return list(dedup.values())

    async def _llm_normalize_batch(self, batch: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        payload = {"query": query, "entities": batch}
        messages = [
            {
                "role": "system",
                "content": (
                    "You normalize pharma expert identities. "
                    "Return JSON list aligned to the order of inputs. "
                    "Include canonical_name, affiliations, type, expertise, optional id/orcid, and contact metadata."
                ),
            },
            {"role": "user", "content": json.dumps(payload)},
        ]
        try:
            raw = await self.llm_call(messages, model=settings.LMSTUDIO_MODEL_NAME)
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "entities" in parsed:
                parsed = parsed["entities"]
            if isinstance(parsed, list):
                return parsed
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.warning("Normalization fallback due to %s", exc)

        return [{} for _ in batch]

    def _collect_entities(self, signals: Dict[str, Any]) -> List[Dict[str, Any]]:
        aggregated: List[Dict[str, Any]] = []
        for channel, payload in (signals or {}).items():
            if not isinstance(payload, dict):
                continue
            for entity in self._ensure_list(payload.get("entities")):
                name = entity.get("name") or entity.get("label")
                if not name:
                    continue
                aggregated.append(
                    {
                        "raw_name": name,
                        "type": entity.get("type") or ("expert" if entity.get("roles") else "institution"),
                        "affiliations": self._ensure_list(entity.get("affiliations") or entity.get("organization")),
                        "expertise": self._ensure_list(entity.get("expertise") or entity.get("domains")),
                        "roles": self._ensure_list(entity.get("roles")),
                        "document_ids": self._ensure_list(entity.get("documents") or entity.get("document_ids")),
                        "trial_ids": self._ensure_list(entity.get("trial_ids")),
                        "patent_ids": self._ensure_list(entity.get("patent_ids")),
                        "web_ids": self._ensure_list(entity.get("web_ids")),
                        "aliases": self._ensure_list(entity.get("aliases")),
                        "contact": entity.get("contact"),
                        "channels": [channel],
                        "evidence": self._ensure_list(entity.get("evidence")),
                        "recent_activity": entity.get("recent_activity", 0),
                    }
                )
        return aggregated

    def _build_entity_nodes(self, entities: List[Dict[str, Any]], query: str) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        nodes: List[Dict[str, Any]] = []
        alias_index: Dict[str, str] = {}
        for entity in entities:
            influence_score, rep_score = self._compute_scores(entity, query)
            entity["score"] = influence_score
            entity["influence_score"] = influence_score
            entity["repurposing_relevance_score"] = rep_score
            node = {
                "id": entity["id"],
                "label": entity["label"],
                "type": entity["type"],
                "affiliations": entity.get("affiliations", []),
                "expertise": entity.get("expertise", []),
                "contact": entity.get("contact"),
                "score": influence_score,
                "influence_score": influence_score,
                "repurposing_relevance_score": rep_score,
                "size": self._scale_size(influence_score),
                "color": self.NODE_COLORS.get(entity["type"], "#4A5568"),
                "metadata": {
                    "document_ids": entity.get("document_ids", []),
                    "trial_ids": entity.get("trial_ids", []),
                    "patent_ids": entity.get("patent_ids", []),
                    "source_channels": entity.get("source_channels", []),
                    "evidence": entity.get("evidence", []),
                },
            }
            nodes.append(node)
            for alias in entity.get("aliases", []):
                if not alias:
                    continue
                alias_index[self._normalize_text(alias)] = entity["id"]
            alias_index[self._normalize_text(entity["label"])] = entity["id"]
        return nodes, alias_index

    def _ingest_context_nodes(self, context_nodes: Dict[str, Dict[str, Any]], signals: Dict[str, Any]) -> None:
        for channel, payload in (signals or {}).items():
            if not isinstance(payload, dict):
                continue

            for institution in self._ensure_list(payload.get("institutions")):
                if isinstance(institution, dict):
                    name = institution.get("name") or institution.get("label")
                    meta = {k: v for k, v in institution.items() if k not in {"name", "label"}}
                else:
                    name = institution
                    meta = {}
                if not name:
                    continue
                node_id = self._make_node_id("institution", name)
                context_nodes.setdefault(
                    node_id,
                    {
                        "id": node_id,
                        "label": name,
                        "type": "institution",
                        "size": 18,
                        "color": self.NODE_COLORS["institution"],
                        "metadata": {"channel": channel, **meta},
                    },
                )

            for event in self._ensure_list(payload.get("events")):
                if not isinstance(event, dict):
                    continue
                if event.get("trial_id") or event.get("nct_id"):
                    trial_id = event.get("trial_id") or event.get("nct_id")
                    label = event.get("title") or trial_id
                    node_id = self._make_node_id("trial", trial_id)
                    context_nodes.setdefault(
                        node_id,
                        {
                            "id": node_id,
                            "label": label,
                            "type": "trial",
                            "size": 16,
                            "color": self.NODE_COLORS["trial"],
                            "metadata": {"phase": event.get("phase"), "channel": channel},
                        },
                    )
                if event.get("patent_number"):
                    patent_no = event["patent_number"]
                    label = event.get("title") or patent_no
                    node_id = self._make_node_id("patent", patent_no)
                    context_nodes.setdefault(
                        node_id,
                        {
                            "id": node_id,
                            "label": label,
                            "type": "patent",
                            "size": 14,
                            "color": self.NODE_COLORS["patent"],
                            "metadata": {"channel": channel, "authority": event.get("authority")},
                        },
                    )

    def _build_affiliation_edges(
        self, entities: List[Dict[str, Any]], context_nodes: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        for entity in entities:
            for affiliation in entity.get("affiliations", []):
                if not affiliation:
                    continue
                node_id = self._make_node_id("institution", affiliation)
                if node_id not in context_nodes:
                    context_nodes[node_id] = {
                        "id": node_id,
                        "label": affiliation,
                        "type": "institution",
                        "size": 18,
                        "color": self.NODE_COLORS["institution"],
                        "metadata": {},
                    }
                edges.append(
                    self._make_edge(
                        source=entity["id"],
                        target=node_id,
                        relation="affiliated_with",
                        evidence=entity.get("evidence", []),
                        weight=0.55,
                    )
                )
        return edges

    def _build_document_edges(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        doc_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for entity in entities:
            for doc_id in entity.get("document_ids", []):
                doc_map[doc_id].append(entity)

        for doc_id, participants in doc_map.items():
            if len(participants) < 2:
                continue
            for i in range(len(participants)):
                for j in range(i + 1, len(participants)):
                    edges.append(
                        self._make_edge(
                            source=participants[i]["id"],
                            target=participants[j]["id"],
                            relation="co_author",
                            evidence=[doc_id],
                            weight=0.4 + 0.1 * min(3, len(participants)),
                        )
                    )
        return edges

    def _build_trial_edges(
        self,
        signals: Dict[str, Any],
        alias_index: Dict[str, str],
        context_nodes: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        for channel, payload in (signals or {}).items():
            for event in self._ensure_list(payload.get("events")):
                if not isinstance(event, dict):
                    continue
                trial_id = event.get("trial_id") or event.get("nct_id")
                if not trial_id:
                    continue
                node_id = self._make_node_id("trial", trial_id)
                if node_id not in context_nodes:
                    context_nodes[node_id] = {
                        "id": node_id,
                        "label": event.get("title") or trial_id,
                        "type": "trial",
                        "size": 16,
                        "color": self.NODE_COLORS["trial"],
                        "metadata": {"phase": event.get("phase"), "channel": channel},
                    }
                investigators = self._ensure_list(event.get("investigators") or event.get("staff"))
                for investigator in investigators:
                    if isinstance(investigator, dict):
                        name = investigator.get("name")
                    else:
                        name = investigator
                    if not name:
                        continue
                    matched = alias_index.get(self._normalize_text(name))
                    if matched:
                        edges.append(
                            self._make_edge(
                                source=matched,
                                target=node_id,
                                relation="investigator_in",
                                evidence=self._ensure_list(event.get("evidence")),
                                weight=0.65,
                            )
                        )
        return edges

    def _build_patent_edges(
        self,
        signals: Dict[str, Any],
        alias_index: Dict[str, str],
        context_nodes: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        for channel, payload in (signals or {}).items():
            patents = self._ensure_list(payload.get("patents"))
            if not patents:
                continue
            for patent in patents:
                if not isinstance(patent, dict):
                    continue
                patent_no = patent.get("patent_number") or patent.get("publication_number")
                if not patent_no:
                    continue
                node_id = self._make_node_id("patent", patent_no)
                if node_id not in context_nodes:
                    context_nodes[node_id] = {
                        "id": node_id,
                        "label": patent.get("title") or patent_no,
                        "type": "patent",
                        "size": 14,
                        "color": self.NODE_COLORS["patent"],
                        "metadata": {"channel": channel, "authority": patent.get("authority")},
                    }
                inventors = self._ensure_list(patent.get("inventors"))
                for inventor in inventors:
                    if isinstance(inventor, dict):
                        name = inventor.get("name") or inventor.get("label")
                    else:
                        name = inventor
                    if not name:
                        continue
                    matched = alias_index.get(self._normalize_text(name))
                    if matched:
                        edges.append(
                            self._make_edge(
                                source=matched,
                                target=node_id,
                                relation="inventor_of",
                                evidence=[patent_no],
                                weight=0.6,
                            )
                        )
                for i in range(len(inventors)):
                    for j in range(i + 1, len(inventors)):
                        first = alias_index.get(self._normalize_text(self._extract_name(inventors[i])))
                        second = alias_index.get(self._normalize_text(self._extract_name(inventors[j])))
                        if first and second:
                            edges.append(
                                self._make_edge(
                                    source=first,
                                    target=second,
                                    relation="co_inventor",
                                    evidence=[patent_no],
                                    weight=0.5,
                                )
                            )
        return edges

    def _build_collaboration_edges(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        for entity in entities:
            shared_trials = set(entity.get("trial_ids", []))
            shared_patents = set(entity.get("patent_ids", []))
            shared_docs = set(entity.get("document_ids", []))
            for counterpart in entities:
                if entity["id"] >= counterpart["id"]:
                    continue
                overlap = (
                    len(shared_trials.intersection(counterpart.get("trial_ids", [])))
                    + len(shared_patents.intersection(counterpart.get("patent_ids", [])))
                    + len(shared_docs.intersection(counterpart.get("document_ids", [])))
                )
                if overlap == 0:
                    continue
                edges.append(
                    self._make_edge(
                        source=entity["id"],
                        target=counterpart["id"],
                        relation="collaborated_with",
                        evidence=list(shared_trials | shared_patents | shared_docs),
                        weight=min(0.9, 0.3 + 0.1 * overlap),
                    )
                )
        return edges

    def _make_edge(
        self,
        source: str,
        target: str,
        relation: str,
        evidence: Optional[List[str]] = None,
        weight: float = 0.4,
    ) -> Dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "type": relation,
            "label": relation,
            "weight": round(min(1.0, max(0.05, weight)), 3),
            "evidence": self._ensure_list(evidence),
        }

    def _compute_scores(self, entity: Dict[str, Any], query: str) -> Tuple[int, int]:
        counters = {
            "publications": len(entity.get("document_ids", [])),
            "trials": len(entity.get("trial_ids", [])),
            "patents": len(entity.get("patent_ids", [])),
            "web_intel": len(entity.get("web_ids", [])),
            "recent_activity": entity.get("recent_activity", 0),
        }
        weighted = sum(self.SCORE_WEIGHTS[key] * counters[key] for key in self.SCORE_WEIGHTS)
        influence = min(100, int(round(weighted)))

        query_tokens = set(self._normalize_text(query).split())
        expertise_tokens = set()
        for tag in entity.get("expertise", []):
            expertise_tokens.update(self._normalize_text(tag).split())
        overlap = len(query_tokens.intersection(expertise_tokens))
        rep_score = min(100, int(40 + 12 * overlap + 3 * counters["trials"]))
        return influence, rep_score

    def _build_recommendations(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ranked = sorted(
            [
                {
                    "id": entity["id"],
                    "name": entity["label"],
                    "affiliations": entity.get("affiliations", []),
                    "expertise": entity.get("expertise", []),
                    "influence_score": entity.get("score", 0),
                    "repurposing_relevance_score": entity.get("repurposing_relevance_score", 0),
                    "reason": self._build_reason(entity),
                }
                for entity in entities
            ],
            key=lambda item: (item["repurposing_relevance_score"], item["influence_score"]),
            reverse=True,
        )
        return ranked[:12]

    def _build_reason(self, entity: Dict[str, Any]) -> str:
        parts = []
        trials = len(entity.get("trial_ids", []))
        patents = len(entity.get("patent_ids", []))
        pubs = len(entity.get("document_ids", []))
        if trials:
            parts.append(f"{trials} active trials")
        if patents:
            parts.append(f"{patents} related patents")
        if pubs:
            parts.append(f"{pubs} publications")
        expertise = ", ".join(entity.get("expertise", [])[:2])
        if expertise:
            parts.append(f"focus on {expertise}")
        return "; ".join(parts) or "Relevant domain activity"

    def _save_graph_file(self, graph_payload: Dict[str, Any]) -> Path:
        file_path = self.graph_dir / f"graph_{graph_payload['graph_id']}.json"
        with file_path.open("w", encoding="utf-8") as fp:
            json.dump(graph_payload, fp, ensure_ascii=False, indent=2)
        return file_path

    async def _persist_metadata(self, graph_id: str, query: str, meta: Dict[str, Any], path: Path) -> None:
        payload = {
            "graph_id": graph_id,
            "created_at": datetime.utcnow(),
            "query": query,
            "node_count": meta.get("node_count", 0),
            "edge_count": meta.get("edge_count", 0),
            "path": str(path),
        }
        try:
            await self.graph_collection.insert_one(payload)
        except Exception as exc:  # pragma: no cover - persistence is best-effort
            self._logger.warning("Unable to persist expert graph summary: %s", exc)

    def _scale_size(self, influence_score: int) -> float:
        return round(12 + math.log2(max(1, influence_score + 1)) * 6, 2)

    def _make_node_id(self, prefix: str, value: str) -> str:
        normalized = self._normalize_text(str(value or "")) or uuid.uuid4().hex
        return f"{prefix}:{normalized}"

    def _normalize_contact(self, primary: Optional[Dict[str, Any]], secondary: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        base = {"email": None, "orcid": None, "confidence": 0.0, "source": None}
        primary = primary or {}
        secondary = secondary or {}
        for field in ("email", "orcid"):
            candidate = primary.get(field) or secondary.get(field)
            if candidate:
                base[field] = candidate
                base["confidence"] = float(primary.get("confidence") or secondary.get("confidence") or 0.65)
                base["source"] = primary.get("source") or secondary.get("source")
        return base

    def _merge_entity_records(self, base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
        for key in ("document_ids", "trial_ids", "patent_ids", "web_ids", "evidence"):
            base[key].update(extra.get(key, set()))
        base["aliases"] = sorted(set(base.get("aliases", [])) | set(extra.get("aliases", [])))
        base["source_channels"] = sorted(set(base.get("source_channels", [])) | set(extra.get("source_channels", [])))
        base["recent_activity"] = max(base.get("recent_activity", 0), extra.get("recent_activity", 0))
        return base

    @staticmethod
    def _extract_name(candidate: Any) -> str:
        if isinstance(candidate, dict):
            return candidate.get("name") or candidate.get("label") or ""
        return str(candidate or "")

    @staticmethod
    def _ensure_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    @staticmethod
    def _make_fingerprint(name: str, affiliations: List[str]) -> str:
        name_norm = GraphBuilder._normalize_text(name)
        aff_norm = "|".join(sorted(GraphBuilder._normalize_text(aff) for aff in affiliations if aff))
        return f"{name_norm}:{aff_norm}"

    @staticmethod
    def _normalize_text(text: Optional[str]) -> str:
        return " ".join(str(text or "").lower().strip().split())


