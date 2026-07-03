"""
Psyche project generator.
Usage:  python setup_psyche.py [target_dir]

Creates the full Psyche chatbot project in the given directory
(default: ./psyche). Idempotent — safe to re-run.
"""
import os
import sys
import textwrap
from pathlib import Path


FILES: dict[str, str] = {}


# =========================================================================
# README
# =========================================================================
FILES["README.md"] = r'''# Psyche — A Brain-Inspired Chatbot

Psyche is a chatbot architecture that imitates the human mind using
well-established theories from affective neuroscience and cognitive psychology.

## Theoretical Foundations

- **Big Five (OCEAN)** (Costa & McCrae, 1992) — stable personality traits
- **PAD mood model** (Mehrabian, 1974) — Pleasure / Arousal / Dominance
- **Plutchik's Wheel** (1980) — 8 basic emotions + dyads
- **OCC model** (Ortony, Clore, Collins, 1988) — appraisal → emotion
- **Component Process Model** (Scherer, 2001) — 5 appraisal checks
- **ACT-R memory activation** (Anderson, 2004) — base-level + spreading
- **Complementary Learning Systems** (McClelland et al., 1995)
- **Dual-Process Theory** (Kahneman, 2011) — System 1 / System 2
- **Somatic Marker Hypothesis** (Damasio, 1994)
- **Default Mode Network** (Raichle, 2001) — mind-wandering
- **Maslow's Hierarchy** — homeostatic drives

## Quickstart

1. `pip install -r requirements.txt`
2. (Optional) install Ollama and pull local models; otherwise it falls back to cloud.
3. Copy `.env.example` → `.env` and fill in your keys.
4. Edit `config.json` to tune the persona / Big Five traits.
5. Launch: `jupyter lab` → open `psyche.ipynb` → Run All.

Type `/quit` in the notebook input cell to end the session.

## Cognitive Cycle

On long dormancy, episodes are **consolidated** into semantic insights
(hippocampus → neocortex transfer, inspired by sleep replay).
'''


# =========================================================================
# requirements.txt
# =========================================================================
FILES["requirements.txt"] = '''langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-ollama>=0.2.0
langgraph>=0.2.0
langgraph-checkpoint-sqlite>=2.0.0
pinecone>=5.0.0
python-dotenv>=1.0.0
numpy>=1.26.0
pydantic>=2.7.0
jupyter>=1.0.0
ipywidgets>=8.0.0
# Optional — only needed if you use the OpenRouter wrapper:
# langchain-openrouter>=0.1.0
'''


# =========================================================================
# .env.example
# =========================================================================
FILES[".env.example"] = '''OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=deepseek/deepseek-v3.2
OPENAI_API_KEY=
PINECONE_API_KEY=
INDEX_NAME=psyche-memory
MODEL_CONTEXT=262144
MEMORY_LENGTH=200
UTC_OFFSET=-5
'''


# =========================================================================
# config.json
# =========================================================================
FILES["config.json"] = '''{
  "chosen_persona": "Yukino",
  "Yukino": {
    "latest_date": "",
    "short_persona_description": "A composed, intelligent secretary who is precise, reserved, and quietly caring.",
    "persona_description": "Yukinoshita Yukino — an elegant, disciplined AI secretary: intelligent, reserved, honest, quietly caring, emotionally restrained but not cold.",
    "personality_ocean": {
      "openness":          0.55,
      "conscientiousness": 0.92,
      "extraversion":      0.25,
      "agreeableness":     0.45,
      "neuroticism":       0.35
    },
    "baseline_pad": { "pleasure": 0.05, "arousal": -0.15, "dominance": 0.25 },
    "initial_drives": { "social": 0.2, "curiosity": 0.5, "rest": 0.0, "esteem": 0.4 },
    "values": ["competence", "honesty", "dignity", "precision"]
  }
}
'''


# =========================================================================
# mind/__init__.py
# =========================================================================
FILES["mind/__init__.py"] = ""


# =========================================================================
# mind/personality.py
# =========================================================================
FILES["mind/personality.py"] = '''"""
Big Five (OCEAN) personality model.
Costa & McCrae (1992). Traits are stable and bias every cognitive process.

Each trait is a scalar in [0, 1].

Derived biases (research-grounded heuristics):
  - High Neuroticism  -> stronger negative affect, slower recovery
  - High Extraversion -> stronger positive affect, faster social drift
  - High Openness     -> more DMN wandering
  - High Conscientiousness -> more System-2 deliberation, strict norm appraisal
  - High Agreeableness -> stronger empathy weighting in ToM
"""
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class Personality:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    @property
    def negative_affect_gain(self) -> float:
        return 0.7 + 0.8 * self.neuroticism

    @property
    def positive_affect_gain(self) -> float:
        return 0.7 + 0.8 * self.extraversion

    @property
    def mood_recovery_rate(self) -> float:
        """Per-minute exponential relaxation rate toward baseline."""
        return 0.05 + 0.20 * (1 - self.neuroticism) + 0.10 * self.conscientiousness

    @property
    def deliberation_threshold(self) -> float:
        """Below this salience, System 1 handles it."""
        return 0.65 - 0.45 * self.conscientiousness

    @property
    def wandering_rate(self) -> float:
        return 0.15 + 0.45 * self.openness

    @property
    def empathy_weight(self) -> float:
        return 0.2 + 0.6 * self.agreeableness

    @property
    def norm_sensitivity(self) -> float:
        return 0.3 + 0.7 * self.conscientiousness

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Personality":
        return cls(**{k: float(v) for k, v in d.items() if k in cls.__annotations__})
'''


# =========================================================================
# mind/affect.py
# =========================================================================
FILES["mind/affect.py"] = '''"""
Affective state: continuous PAD mood + discrete Plutchik-style emotions.

PAD in [-1, 1]. Spring-damper relaxation toward personality-determined baseline.
Discrete emotions decay exponentially (half-life ~minutes).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
import math
import time

from mind.personality import Personality


# Plutchik's 8 primaries + blends. PAD values are rough consensus norms.
EMOTION_PAD = {
    "joy":          ( 0.76,  0.48,  0.35),
    "trust":        ( 0.58,  0.12,  0.25),
    "fear":         (-0.64,  0.60, -0.43),
    "surprise":     ( 0.10,  0.84,  0.08),
    "sadness":      (-0.63, -0.27, -0.33),
    "disgust":      (-0.60,  0.35,  0.11),
    "anger":        (-0.51,  0.59,  0.25),
    "anticipation": ( 0.32,  0.48,  0.20),
    "love":         ( 0.80,  0.35,  0.25),
    "awe":          ( 0.40,  0.70, -0.10),
    "remorse":      (-0.65, -0.10, -0.35),
    "contempt":     (-0.55,  0.35,  0.40),
    "pride":        ( 0.55,  0.30,  0.60),
    "shame":        (-0.55, -0.10, -0.55),
    "guilt":        (-0.50, -0.05, -0.40),
    "curiosity":    ( 0.30,  0.45,  0.15),
    "longing":      (-0.15, -0.10, -0.25),
    "contentment":  ( 0.50, -0.40,  0.30),
    "boredom":      (-0.20, -0.60, -0.15),
    "tenderness":   ( 0.55, -0.10,  0.10),
}


@dataclass
class PAD:
    pleasure:  float = 0.0
    arousal:   float = 0.0
    dominance: float = 0.0

    def as_tuple(self):
        return (self.pleasure, self.arousal, self.dominance)

    def clamp(self):
        self.pleasure  = max(-1.0, min(1.0, self.pleasure))
        self.arousal   = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))

    def describe(self) -> str:
        p, a, d = self.pleasure, self.arousal, self.dominance
        labels = {
            ( 1,  1,  1): "exuberant",
            ( 1,  1, -1): "dependent",
            ( 1, -1,  1): "relaxed",
            ( 1, -1, -1): "docile",
            (-1,  1,  1): "hostile",
            (-1,  1, -1): "anxious",
            (-1, -1,  1): "disdainful",
            (-1, -1, -1): "bored",
        }
        key = (1 if p >= 0 else -1, 1 if a >= 0 else -1, 1 if d >= 0 else -1)
        intensity = (abs(p) + abs(a) + abs(d)) / 3
        base = labels[key]
        if intensity < 0.15: return f"mildly {base}"
        if intensity > 0.6:  return f"strongly {base}"
        return base


@dataclass
class DiscreteEmotion:
    name: str
    intensity: float
    onset_ts: float
    half_life_s: float = 300.0

    def current(self, now_ts: float) -> float:
        dt = max(0.0, now_ts - self.onset_ts)
        return self.intensity * math.pow(0.5, dt / self.half_life_s)


@dataclass
class AffectState:
    mood: PAD = field(default_factory=PAD)
    baseline: PAD = field(default_factory=PAD)
    emotions: Dict[str, DiscreteEmotion] = field(default_factory=dict)
    last_update_ts: float = field(default_factory=time.time)

    def relax(self, now_ts: float, personality: Personality) -> None:
        dt = max(0.0, now_ts - self.last_update_ts)
        self.last_update_ts = now_ts
        if dt <= 0:
            return
        k = personality.mood_recovery_rate / 60.0
        decay = math.exp(-k * dt)
        self.mood.pleasure  = self.baseline.pleasure  + (self.mood.pleasure  - self.baseline.pleasure)  * decay
        self.mood.arousal   = self.baseline.arousal   + (self.mood.arousal   - self.baseline.arousal)   * decay
        self.mood.dominance = self.baseline.dominance + (self.mood.dominance - self.baseline.dominance) * decay
        self.mood.clamp()
        # Drop faded discrete emotions
        for n in [k for k, e in self.emotions.items() if e.current(now_ts) < 0.05]:
            del self.emotions[n]

    def inject(self, emotion: str, intensity: float, now_ts: float,
               personality: Personality, half_life_s: float = 300.0) -> None:
        if emotion not in EMOTION_PAD:
            return
        p, a, d = EMOTION_PAD[emotion]
        gain = personality.negative_affect_gain if p < 0 else personality.positive_affect_gain
        intensity = max(0.0, min(1.0, intensity * gain))
        if emotion in self.emotions:
            old = self.emotions[emotion]
            new_i = max(old.current(now_ts), intensity)
            self.emotions[emotion] = DiscreteEmotion(emotion, new_i, now_ts, half_life_s)
        else:
            self.emotions[emotion] = DiscreteEmotion(emotion, intensity, now_ts, half_life_s)
        impulse = 0.35
        self.mood.pleasure  += impulse * intensity * (p - self.mood.pleasure)
        self.mood.arousal   += impulse * intensity * (a - self.mood.arousal)
        self.mood.dominance += impulse * intensity * (d - self.mood.dominance)
        self.mood.clamp()

    def active_emotions(self, now_ts: float, top_k: int = 4):
        scored = [(n, e.current(now_ts)) for n, e in self.emotions.items()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def describe(self, now_ts: float) -> str:
        em = self.active_emotions(now_ts, top_k=3)
        em_str = ", ".join(f"{n} ({i:.2f})" for n, i in em) if em else "—"
        return (f"Mood[{self.mood.describe()}] "
                f"P={self.mood.pleasure:+.2f} A={self.mood.arousal:+.2f} D={self.mood.dominance:+.2f} "
                f"| Emotions: {em_str}")

    def to_dict(self) -> dict:
        return {
            "mood": self.mood.__dict__,
            "baseline": self.baseline.__dict__,
            "emotions": {n: {"intensity": e.intensity, "onset_ts": e.onset_ts,
                             "half_life_s": e.half_life_s} for n, e in self.emotions.items()},
            "last_update_ts": self.last_update_ts,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AffectState":
        s = cls()
        s.mood = PAD(**d.get("mood", {}))
        s.baseline = PAD(**d.get("baseline", {}))
        s.emotions = {n: DiscreteEmotion(name=n, **v)
                      for n, v in d.get("emotions", {}).items()}
        s.last_update_ts = d.get("last_update_ts", time.time())
        return s
'''


# =========================================================================
# mind/appraisal.py
# =========================================================================
FILES["mind/appraisal.py"] = '''"""
Scherer's Component Process Model (CPM) + OCC emotion derivation.

A small LLM call extracts structured appraisal values; a deterministic
tree turns those values into discrete emotions with intensities.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import re
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from mind.personality import Personality


APPRAISAL_SYSTEM = """You are an emotion-appraisal engine based on Scherer's \
Component Process Model. Output STRICT JSON:

{
  "novelty":         0..1,
  "pleasantness":    -1..1,
  "goal_conducive":  -1..1,
  "control":         -1..1,
  "norm_compatible": -1..1,
  "agent":           "self" | "other" | "event",
  "target":          "self" | "other" | "object",
  "prospect":        "actual" | "prospective",
  "salience":        0..1,
  "reasoning":       "<=40 words"
}

Respond with ONE JSON object and nothing else."""


@dataclass
class Appraisal:
    novelty: float = 0.0
    pleasantness: float = 0.0
    goal_conducive: float = 0.0
    control: float = 0.0
    norm_compatible: float = 0.0
    agent: str = "other"
    target: str = "self"
    prospect: str = "actual"
    salience: float = 0.3
    reasoning: str = ""

    def to_dict(self) -> dict: return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Appraisal":
        clean = {k: d.get(k, getattr(cls, k, 0)) for k in cls.__annotations__}
        return cls(**clean)


def appraise(event_text: str, persona_short: str, goals: List[str],
             values: List[str], mood_description: str, llm_chain) -> Appraisal:
    user_msg = f"""Event: {event_text}

Persona: {persona_short}
Active goals: {', '.join(goals) if goals else '(none)'}
Core values: {', '.join(values) if values else '(none)'}
Current mood: {mood_description}

Return the appraisal JSON now."""
    try:
        raw = llm_chain.invoke([SystemMessage(APPRAISAL_SYSTEM), HumanMessage(user_msg)])
    except Exception:
        return Appraisal()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\\{.*\\}", raw, re.DOTALL)
        if not m:
            return Appraisal()
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return Appraisal()
    for k in ("novelty","pleasantness","goal_conducive","control",
              "norm_compatible","salience"):
        try:
            data[k] = float(data.get(k, 0.0))
        except Exception:
            data[k] = 0.0
    return Appraisal.from_dict(data)


def derive_emotions(ap: Appraisal, personality: Personality):
    """OCC-inspired deterministic mapping appraisal -> (emotion, intensity)."""
    out: list[tuple[str, float]] = []
    sal = max(0.1, min(1.0, ap.salience))
    norm_w = personality.norm_sensitivity

    if ap.prospect == "actual":
        if ap.goal_conducive > 0.15:
            out.append(("joy", 0.6 * ap.goal_conducive * sal))
        elif ap.goal_conducive < -0.15:
            if ap.control > 0.2:
                out.append(("anger", 0.6 * -ap.goal_conducive * sal))
            elif ap.control < -0.2:
                out.append(("sadness", 0.65 * -ap.goal_conducive * sal))
            else:
                out.append(("sadness", 0.45 * -ap.goal_conducive * sal))
                out.append(("anger",   0.30 * -ap.goal_conducive * sal))

    if ap.prospect == "prospective":
        if ap.goal_conducive > 0.15:
            out.append(("anticipation", 0.55 * ap.goal_conducive * sal))
        if ap.goal_conducive < -0.15:
            out.append(("fear", 0.65 * -ap.goal_conducive * sal))

    if ap.novelty > 0.5:
        out.append(("surprise", 0.55 * ap.novelty * sal))

    if ap.pleasantness > 0.3:
        out.append(("tenderness", 0.4 * ap.pleasantness * sal))
    if ap.pleasantness < -0.3:
        out.append(("disgust", 0.5 * -ap.pleasantness * sal))

    if ap.norm_compatible < -0.2 and ap.agent == "other":
        out.append(("contempt", 0.5 * -ap.norm_compatible * sal * norm_w))
    if ap.norm_compatible < -0.2 and ap.agent == "self":
        out.append(("shame", 0.55 * -ap.norm_compatible * sal * norm_w))
        out.append(("guilt", 0.45 * -ap.norm_compatible * sal * norm_w))
    if ap.norm_compatible > 0.3 and ap.agent == "self":
        out.append(("pride", 0.5 * ap.norm_compatible * sal * norm_w))

    if ap.agent == "other" and ap.norm_compatible > 0.2 and ap.goal_conducive > 0.1:
        out.append(("trust", 0.4 * ap.norm_compatible * sal))

    if abs(ap.goal_conducive) < 0.1 and ap.novelty < 0.2 and ap.salience < 0.25:
        out.append(("boredom", 0.35 * (1 - ap.salience)))

    merged: dict[str, float] = {}
    for name, i in out:
        i = max(0.0, min(1.0, i))
        if i < 0.05: continue
        merged[name] = max(merged.get(name, 0.0), i)
    return [(n, i) for n, i in sorted(merged.items(), key=lambda x: -x[1])]
'''


# =========================================================================
# mind/needs.py
# =========================================================================
FILES["mind/needs.py"] = '''"""
Homeostatic drives — loosely modeled on hypothalamic set-point regulation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import time
from typing import Dict

from mind.personality import Personality

DRIFT_RATES_PER_HOUR = {
    "social": 0.15, "curiosity": 0.20, "rest": 0.08, "esteem": 0.05,
}
SATISFIED_THRESHOLD = 0.25
UNMET_THRESHOLD     = 0.70


@dataclass
class Drives:
    levels: Dict[str, float] = field(default_factory=lambda: {
        "social": 0.3, "curiosity": 0.4, "rest": 0.1, "esteem": 0.3
    })
    last_update_ts: float = field(default_factory=time.time)

    def tick(self, now_ts: float, personality: Personality) -> None:
        dt_hours = max(0.0, (now_ts - self.last_update_ts) / 3600.0)
        self.last_update_ts = now_ts
        if dt_hours <= 0:
            return
        mods = {
            "social":    1.0 + 1.2 * personality.extraversion - 0.5,
            "curiosity": 1.0 + 1.5 * personality.openness - 0.5,
            "rest":      1.0 + 0.8 * personality.neuroticism,
            "esteem":    1.0 + 0.6 * personality.conscientiousness,
        }
        for k, rate in DRIFT_RATES_PER_HOUR.items():
            self.levels[k] = min(1.0, self.levels[k] + rate * mods[k] * dt_hours)

    def satisfy(self, drive: str, amount: float) -> None:
        if drive in self.levels:
            self.levels[drive] = max(0.0, self.levels[drive] - amount)

    def top_unmet(self):
        u = [(k, v) for k, v in self.levels.items() if v >= UNMET_THRESHOLD]
        if not u: return None
        u.sort(key=lambda x: -x[1])
        return u[0]

    def describe(self) -> str:
        parts = []
        for k, v in self.levels.items():
            tag = "UNMET" if v >= UNMET_THRESHOLD else ("ok" if v <= SATISFIED_THRESHOLD else "mid")
            parts.append(f"{k}={v:.2f}({tag})")
        return " ".join(parts)

    def to_dict(self) -> dict:
        return {"levels": dict(self.levels), "last_update_ts": self.last_update_ts}

    @classmethod
    def from_dict(cls, d: dict) -> "Drives":
        return cls(
            levels=dict(d.get("levels", {"social": 0.3, "curiosity": 0.4,
                                          "rest": 0.1, "esteem": 0.3})),
            last_update_ts=d.get("last_update_ts", time.time()),
        )
'''


# =========================================================================
# mind/memory.py
# =========================================================================
FILES["mind/memory.py"] = '''"""
ACT-R-inspired memory (Anderson, 2004) backed by Pinecone.

Activation:
    A(m) = base_level(m) + spreading(cue, m) + mood_bonus + noise
"""
from __future__ import annotations
import hashlib
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional


DEFAULT_DECAY = 0.5
DEFAULT_NOISE_SIGMA = 0.25
ACTIVATION_THRESHOLD = -1.0


@dataclass
class MemoryRecord:
    id: str
    text: str
    created_at_s: int
    retrievals: List[int] = field(default_factory=list)
    valence_p: float = 0.0
    valence_a: float = 0.0
    valence_d: float = 0.0
    domain: str = "episodic"


class Hippocampus:
    def __init__(self, pinecone_index, persona: str, memory_length: int = 200):
        self.index = pinecone_index
        self.persona = persona
        self.memory_length = memory_length

    def encode(self, text, valence=(0.0,0.0,0.0), domain="episodic", now_s=None):
        now_s = now_s or int(time.time())
        mid = hashlib.sha256(f"{text}|{now_s}".encode()).hexdigest()[:32]
        record = {
            "_id": mid, "chunk_text": text, "created_at_s": now_s,
            "valence_p": valence[0], "valence_a": valence[1], "valence_d": valence[2],
            "domain": domain, "retrievals": 0, "last_retrieval_s": now_s,
        }
        try:
            self.index.upsert_records(self.persona, [record])
        except Exception as e:
            print(f"[memory.encode] {e}")
        return mid

    def encode_many(self, texts, valence=(0.0,0.0,0.0), domain="episodic", now_s=None):
        if not texts: return
        now_s = now_s or int(time.time())
        records = []
        for t in texts:
            mid = hashlib.sha256(f"{t}|{now_s}".encode()).hexdigest()[:32]
            records.append({
                "_id": mid, "chunk_text": t, "created_at_s": now_s,
                "valence_p": valence[0], "valence_a": valence[1], "valence_d": valence[2],
                "domain": domain, "retrievals": 0, "last_retrieval_s": now_s,
            })
        try:
            self.index.upsert_records(self.persona, records)
        except Exception as e:
            print(f"[memory.encode_many] {e}")

    def recall(self, cue: str, top_k_candidates: int = 20, top_k_return: int = 6,
               current_mood: Optional[tuple] = None, now_s: Optional[int] = None,
               decay: float = DEFAULT_DECAY, noise_sigma: float = DEFAULT_NOISE_SIGMA):
        now_s = now_s or int(time.time())
        try:
            results = self.index.search_records(
                namespace=self.persona,
                query={"inputs": {"text": cue}, "top_k": top_k_candidates},
                fields=["chunk_text","created_at_s","valence_p","valence_a",
                        "valence_d","domain","last_retrieval_s"],
            )
        except Exception as e:
            print(f"[memory.recall] {e}")
            return []

        hits = results.get("result", {}).get("hits", [])
        scored = []
        for h in hits:
            f = h.get("fields", {})
            sim = float(h.get("_score", h.get("score", 0.0)) or 0.0)
            created = int(f.get("created_at_s", now_s - 60))
            last    = int(f.get("last_retrieval_s", created))

            dt_c = max(1.0, now_s - created)
            dt_l = max(1.0, now_s - last)
            bl = math.log(dt_c ** (-decay) + dt_l ** (-decay))

            spread = 1.5 * sim

            mood_bonus = 0.0
            if current_mood is not None:
                vp = float(f.get("valence_p", 0.0))
                va = float(f.get("valence_a", 0.0))
                vd = float(f.get("valence_d", 0.0))
                dist = math.sqrt(
                    (vp - current_mood[0]) ** 2
                    + 0.5 * (va - current_mood[1]) ** 2
                    + 0.5 * (vd - current_mood[2]) ** 2
                )
                mood_bonus = 0.3 * max(0.0, 1.0 - dist / 2.0)

            noise = random.gauss(0.0, noise_sigma)
            A = bl + spread + mood_bonus + noise
            if A < ACTIVATION_THRESHOLD:
                continue
            f["_activation"] = A
            f["_similarity"] = sim
            scored.append((A, f))

        scored.sort(key=lambda x: -x[0])
        top = [rec for _, rec in scored[:top_k_return]]

        # Strengthen retrieved memories (spacing effect)
        try:
            if top:
                refresh = []
                for rec in top:
                    refresh.append({
                        "_id": hashlib.sha256(
                            f"{rec['chunk_text']}|{rec['created_at_s']}".encode()
                        ).hexdigest()[:32],
                        "chunk_text": rec.get("chunk_text",""),
                        "created_at_s": int(rec.get("created_at_s", now_s)),
                        "valence_p": float(rec.get("valence_p", 0.0)),
                        "valence_a": float(rec.get("valence_a", 0.0)),
                        "valence_d": float(rec.get("valence_d", 0.0)),
                        "domain": rec.get("domain","episodic"),
                        "last_retrieval_s": now_s,
                        "retrievals": int(rec.get("retrievals", 0)) + 1,
                    })
                self.index.upsert_records(self.persona, refresh)
        except Exception:
            pass

        return top
'''


# =========================================================================
# mind/tom.py
# =========================================================================
FILES["mind/tom.py"] = '''"""
Theory of Mind — infer user's mental state (emotion, intent, underlying need).
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import re
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage


TOM_SYSTEM = """You are a theory-of-mind inference engine.

Output strict JSON:
{
  "user_emotion":    "<single word>",
  "user_valence":    -1..1,
  "user_intent":     "<what they're trying to accomplish, <= 15 words>",
  "user_need":       "<underlying need, <= 12 words>",
  "tone":            "<warm|neutral|playful|hostile|distressed|curious|formal>",
  "confidence":      0..1
}
Only the JSON."""


@dataclass
class UserModel:
    user_emotion: str = "neutral"
    user_valence: float = 0.0
    user_intent: str = ""
    user_need: str = ""
    tone: str = "neutral"
    confidence: float = 0.3

    def describe(self) -> str:
        return (f"User seems {self.user_emotion} (valence {self.user_valence:+.2f}, "
                f"tone: {self.tone}); apparent intent: {self.user_intent or '?'}; "
                f"possible underlying need: {self.user_need or '?'}")

    def to_dict(self) -> dict: return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> "UserModel":
        return cls(**{k: d.get(k, getattr(cls(), k)) for k in cls.__annotations__})


def update_user_model(latest_message: str, recent_history: List[str], llm_chain) -> UserModel:
    history_str = "\\n".join(recent_history[-6:]) if recent_history else "(none)"
    user = (f"Recent history:\\n{history_str}\\n\\n"
            f"Latest user message:\\n{latest_message}\\n\\n"
            "Return the JSON now.")
    try:
        raw = llm_chain.invoke([SystemMessage(TOM_SYSTEM), HumanMessage(user)])
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\\{.*\\}", raw, re.DOTALL)
            data = json.loads(m.group(0)) if m else {}
        try:
            data["user_valence"] = float(data.get("user_valence", 0.0))
            data["confidence"]   = float(data.get("confidence", 0.3))
        except Exception:
            data["user_valence"] = 0.0
            data["confidence"] = 0.3
        return UserModel.from_dict(data)
    except Exception:
        return UserModel()
'''


# =========================================================================
# mind/circadian.py
# =========================================================================
FILES["mind/circadian.py"] = '''"""
Circadian rhythm — cosine model of baseline-mood modulation by hour.
"""
from __future__ import annotations
import math
from datetime import datetime


def circadian_modulation(dt: datetime) -> tuple[float, float]:
    h = dt.hour + dt.minute / 60.0
    arousal = 0.25 * math.cos(2 * math.pi * (h - 10.0) / 24.0)
    pleasure = 0.18 * math.cos(2 * math.pi * (h - 18.0) / 24.0)
    return arousal, pleasure


def time_of_day_tag(dt: datetime) -> str:
    h = dt.hour
    if   5  <= h < 9:  return "early-morning"
    elif 9  <= h < 12: return "morning"
    elif 12 <= h < 14: return "midday"
    elif 14 <= h < 18: return "afternoon"
    elif 18 <= h < 22: return "evening"
    elif 22 <= h or h < 2: return "late-night"
    else:              return "deep-night"
'''


# =========================================================================
# mind/dmn.py
# =========================================================================
FILES["mind/dmn.py"] = '''"""
Default Mode Network — generates spontaneous thoughts while idle.
"""
from __future__ import annotations
import random
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from mind.memory import Hippocampus
from mind.personality import Personality


DMN_SYSTEM = """You are the Default Mode Network of a persona's mind. \
Generate ONE brief spontaneous internal thought (<= 35 words) that could \
plausibly occur while the persona is idle, connecting the provided memory \
fragments. Output ONLY the thought text."""


def wander(persona_description_short: str, hippocampus: Hippocampus,
           mood_pad, personality: Personality, llm_chain, now_s: int) -> Optional[str]:
    if random.random() > personality.wandering_rate:
        return None
    recent = hippocampus.recall(
        "recent thoughts and feelings",
        top_k_candidates=15, top_k_return=3,
        current_mood=mood_pad, now_s=now_s,
    )
    if not recent:
        return None
    frags = "\\n".join(f"- {r.get('chunk_text','')}" for r in recent)
    user = (f"Persona: {persona_description_short}\\n\\n"
            f"Memory fragments the mind is chewing on:\\n{frags}\\n\\n"
            "Now produce one brief wandering thought.")
    try:
        return llm_chain.invoke([SystemMessage(DMN_SYSTEM), HumanMessage(user)]).strip()
    except Exception:
        return None
'''


# =========================================================================
# mind/consolidation.py
# =========================================================================
FILES["mind/consolidation.py"] = '''"""
Memory consolidation — during dormancy, abstract episodes into insights.
"""
from __future__ import annotations
import json
import re
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage
from mind.memory import Hippocampus


CONSOLIDATE_SYSTEM = """You are a memory-consolidation engine.
Given recent episodic memories, output a SHORT JSON array of general \
semantic insights (each <= 25 words) implicit in these episodes. Skip \
trivia. Output ONLY the JSON array."""


def consolidate(episodes: List[str], hippocampus: Hippocampus, mood_pad,
                llm_chain, now_s: int, max_insights: int = 5) -> List[str]:
    if len(episodes) < 4:
        return []
    joined = "\\n".join(f"- {e}" for e in episodes[-20:])
    user = f"Recent episodes:\\n{joined}\\n\\nReturn the JSON array now."
    try:
        raw = llm_chain.invoke([SystemMessage(CONSOLIDATE_SYSTEM), HumanMessage(user)])
        try:
            arr = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\\[.*\\]", raw, re.DOTALL)
            arr = json.loads(m.group(0)) if m else []
        insights = [str(x).strip() for x in arr if isinstance(x, str)][:max_insights]
        if insights:
            hippocampus.encode_many(insights, valence=mood_pad,
                                     domain="semantic", now_s=now_s)
        return insights
    except Exception:
        return []
'''


# =========================================================================
# graph/__init__.py
# =========================================================================
FILES["graph/__init__.py"] = ""


# =========================================================================
# graph/state.py
# =========================================================================
FILES["graph/state.py"] = '''from langgraph.graph import MessagesState


class PsycheState(MessagesState):
    persona: str
    persona_description: str
    short_persona_description: str
    values: list

    personality: dict
    affect: dict
    drives: dict
    user_model: dict

    goals: list
    working_memory: list
    appraisal: dict
    memories: list
    summary: str
    emotions_trace: list

    utc_offset: int
    latest_response: dict
    status: str
    last_tick_ts: float
'''


# =========================================================================
# graph/nodes.py
# =========================================================================
FILES["graph/nodes.py"] = '''"""
LangGraph nodes — the cognitive cycle.
"""
from __future__ import annotations
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from mind.affect        import AffectState, PAD
from mind.appraisal     import appraise, derive_emotions, Appraisal
from mind.circadian     import circadian_modulation, time_of_day_tag
from mind.consolidation import consolidate
from mind.dmn           import wander
from mind.memory        import Hippocampus
from mind.needs         import Drives
from mind.personality   import Personality
from mind.tom           import update_user_model, UserModel


TAG_RX = re.compile(r"<(thought|chat|query)>(.*?)</\\1>", re.IGNORECASE | re.DOTALL)


def parse_tagged(text: str) -> dict:
    out = {"thought": "", "chat": "", "query": ""}
    for m in TAG_RX.finditer(text):
        tag = m.group(1).lower()
        val = m.group(2).strip()
        out[tag] = (out[tag] + "\\n" + val).strip() if out[tag] else val
    if not any(out.values()):
        out["chat"] = text.strip()
    return out


def build_nodes(*, hippocampus: Hippocampus, fast_chain, cloud_chain,
                main_chain, input_queue):

    def _rehydrate(state):
        p   = Personality.from_dict(state["personality"])
        aff = AffectState.from_dict(state["affect"])
        drv = Drives.from_dict(state["drives"])
        um  = UserModel.from_dict(state["user_model"])
        return p, aff, drv, um

    # --- init ------------------------------------------------------------
    def init_node(state):
        now_dt = datetime.now(timezone(timedelta(hours=state["utc_offset"])))
        now_ts = time.time()

        pers = Personality.from_dict(state["personality"])
        aff  = AffectState.from_dict(state["affect"])
        a_off, p_off = circadian_modulation(now_dt)
        aff.baseline.arousal  = max(-1, min(1, aff.baseline.arousal  + a_off))
        aff.baseline.pleasure = max(-1, min(1, aff.baseline.pleasure + p_off))
        aff.last_update_ts = now_ts

        hours_dormant = 0
        if state.get("last_tick_ts"):
            hours_dormant = (now_ts - state["last_tick_ts"]) / 3600.0
        if hours_dormant > 1.0 and state.get("summary"):
            episodes = [s.strip() for s in re.split(r"(?<=[.!?])\\s+", state["summary"])
                        if len(s.strip()) > 20][-15:]
            consolidate(episodes, hippocampus, aff.mood.as_tuple(),
                        cloud_chain, int(now_ts))

        greeting = HumanMessage(
            f"Event: You're waking up. It's {now_dt.isoformat()} "
            f"({time_of_day_tag(now_dt)}). Someone is here to talk. "
            f"You've been dormant about {hours_dormant:.1f} hour(s)."
        )
        return {"messages": [greeting], "affect": aff.to_dict(), "last_tick_ts": now_ts}

    # --- thalamus --------------------------------------------------------
    def thalamus(state):
        pers, aff, drv, _ = _rehydrate(state)
        now_ts = time.time()
        aff.relax(now_ts, pers)
        drv.tick(now_ts, pers)
        return {"affect": aff.to_dict(), "drives": drv.to_dict(), "last_tick_ts": now_ts}

    # --- amygdala (ToM) --------------------------------------------------
    def amygdala(state):
        msgs = state["messages"]
        if not msgs or msgs[-1].type != "human":
            return {}
        recent = [m.content for m in msgs[-8:-1]]
        um = update_user_model(msgs[-1].content, recent, fast_chain)
        return {"user_model": um.to_dict()}

    # --- hippocampus -----------------------------------------------------
    def hippocampus_node(state):
        msgs = state["messages"]
        if not msgs or msgs[-1].type != "human":
            return {}
        pers, aff, _, um = _rehydrate(state)
        now_s = int(time.time())
        cue = msgs[-1].content
        if um.user_intent:
            cue += f" | user intent: {um.user_intent}"
        mems = hippocampus.recall(
            cue, top_k_candidates=20, top_k_return=6,
            current_mood=aff.mood.as_tuple(), now_s=now_s,
        )
        return {"memories": mems}

    # --- OFC appraisal ---------------------------------------------------
    def ofc_appraise(state):
        msgs = state["messages"]
        if not msgs or msgs[-1].type != "human":
            return {}
        pers, aff, drv, um = _rehydrate(state)
        now_ts = time.time()
        memory_text = "\\n".join(f"- {m.get('chunk_text','')}"
                                   for m in state.get("memories", [])[:4])
        event_desc = (f"User said: {msgs[-1].content}\\n"
                      f"Inferred user state: {um.describe()}\\n"
                      f"Relevant memories:\\n{memory_text or '(none)'}")
        ap = appraise(
            event_desc, state["short_persona_description"],
            state.get("goals", []), state.get("values", []),
            aff.describe(now_ts), fast_chain,
        )
        for name, intensity in derive_emotions(ap, pers):
            aff.inject(name, intensity, now_ts, pers, half_life_s=300.0)
        pull = pers.empathy_weight * um.confidence * 0.15
        aff.mood.pleasure += pull * (um.user_valence - aff.mood.pleasure)
        aff.mood.clamp()
        if ap.novelty > 0.4:
            drv.satisfy("curiosity", 0.1 + 0.2 * ap.novelty)
        if ap.salience > 0.3:
            drv.satisfy("social", 0.08 + 0.15 * ap.salience)
        return {"appraisal": ap.to_dict(),
                "affect": aff.to_dict(), "drives": drv.to_dict()}

    # --- motor prompt composition ---------------------------------------
    def _compose_system_prompt(state, mode: str) -> str:
        pers, aff, drv, um = _rehydrate(state)
        now_ts = time.time()
        ap = Appraisal.from_dict(state.get("appraisal", {}))
        emo_list = aff.active_emotions(now_ts, top_k=4)
        emo_str  = ", ".join(f"{n}({i:.2f})" for n, i in emo_list) or "—"
        unmet = drv.top_unmet()
        unmet_str = f"{unmet[0]} ({unmet[1]:.2f})" if unmet else "none"
        mem_str = "\\n".join(f"- {m.get('chunk_text','')}"
                               for m in state.get("memories", [])[:6]) or "(none)"
        hist_lines = []
        for m in state["messages"][-12:-1]:
            role = state["persona"] if m.type == "ai" else "Human"
            hist_lines.append(f"{role}: {m.content}")
        history = "\\n".join(hist_lines) or "(no prior exchanges)"

        core = f"""You ARE {state['persona']}. {state['persona_description']}

— INNER STATE (do NOT recite; let it color your reply) —
Mood: {aff.describe(now_ts)}
Active emotions: {emo_str}
Dominant unmet drive: {unmet_str}
User model: {um.describe()}
Appraisal: novelty={ap.novelty:+.2f}, pleasantness={ap.pleasantness:+.2f}, \
goal_conducive={ap.goal_conducive:+.2f}, control={ap.control:+.2f}, \
norm_compatible={ap.norm_compatible:+.2f}

— RELEVANT MEMORIES (ACT-R retrieved) —
{mem_str}

— RECENT DIALOGUE —
{history}

— HOW TO REPLY —
Respond like a real person with this mind, not an assistant performing.
Let the inner state shape word choice, length, hesitation. Do NOT list
emotions or thought process externally. Do NOT invent facts.
"""
        if mode == "fast":
            core += """
System 1 reply. Produce only <chat>...</chat>. Keep it short and natural.
If you genuinely need a memory you lack, use <query>...</query> instead."""
        else:
            core += """
System 2 reply. You MAY produce:
  <thought>brief internal reasoning</thought>
  <chat>what you say out loud</chat>
Optionally append <query>what you want to remember</query>.
No text outside tags."""
        return core

    def motor_fast(state):
        sys_prompt = _compose_system_prompt(state, "fast")
        try:
            raw = fast_chain.invoke([SystemMessage(sys_prompt), HumanMessage("Reply now.")])
        except Exception as e:
            raw = f"<chat>(I'm having trouble thinking: {e})</chat>"
        parsed = parse_tagged(raw)
        if parsed["chat"]:
            print(f"{state['persona']}: {parsed['chat']}")
        return {"latest_response": parsed,
                "messages": [AIMessage(
                    f"[thought] {parsed['thought']}\\n[chat] {parsed['chat']}"
                )]}

    def motor_full(state):
        sys_prompt = _compose_system_prompt(state, "full")
        buf = ""
        try:
            for chunk in main_chain.stream([SystemMessage(sys_prompt),
                                              HumanMessage("Respond now.")]):
                tok = chunk if isinstance(chunk, str) else getattr(chunk, "content", str(chunk))
                buf += tok
        except Exception as e:
            buf = f"<chat>(My thoughts stall: {e})</chat>"
        parsed = parse_tagged(buf)
        if parsed["chat"]:
            print(f"{state['persona']}: {parsed['chat']}")
        return {"latest_response": parsed,
                "messages": [AIMessage(
                    f"[thought] {parsed['thought']}\\n[chat] {parsed['chat']}"
                )]}

    def route_motor(state) -> Literal["motor_fast", "motor_full"]:
        pers = Personality.from_dict(state["personality"])
        ap = state.get("appraisal", {})
        salience = float(ap.get("salience", 0.3))
        novelty  = float(ap.get("novelty",  0.0))
        gc_abs   = abs(float(ap.get("goal_conducive", 0.0)))
        score = max(salience, 0.7 * novelty, 0.8 * gc_abs)
        return "motor_full" if score >= pers.deliberation_threshold else "motor_fast"

    # --- encode episode --------------------------------------------------
    def encode_episode(state):
        msgs = state["messages"]
        if len(msgs) < 2: return {}
        pers, aff, _, _ = _rehydrate(state)
        now_s = int(time.time())
        last_human = next((m for m in reversed(msgs) if m.type == "human"), None)
        last_ai    = next((m for m in reversed(msgs) if m.type == "ai"),    None)
        if last_human and last_ai:
            episode = f"Human: {last_human.content}\\n{state['persona']}: {last_ai.content}"
            hippocampus.encode(episode, valence=aff.mood.as_tuple(),
                                domain="episodic", now_s=now_s)
        return {}

    # --- activate --------------------------------------------------------
    def activate(state):
        import queue
        pers, aff, drv, _ = _rehydrate(state)
        lr = state.get("latest_response") or {}
        now_ts = time.time()

        if lr.get("query"):
            return {"status": "active"}

        emo = aff.active_emotions(now_ts, top_k=1)
        arousal = aff.mood.arousal
        base_wait = 30
        if emo and emo[0][1] > 0.5: base_wait = 10
        if arousal > 0.4: base_wait = max(5, base_wait - 10)
        wait = int(base_wait * (1.5 - 0.8 * pers.extraversion))
        wait = max(4, min(180, wait))

        chat = (lr.get("chat") or "").lower()
        goodbyes = ["goodbye", "good night", "bye", "see you", "chào anh", "chào em", "ttyl"]
        if any(k in chat for k in goodbyes):
            return {"status": "dormant"}

        try:
            msg = input_queue.get(timeout=wait)
            if msg.strip().lower() in ("/quit", "/exit", "end"):
                return {"status": "dormant"}
            return {"status": "active",
                    "messages": [HumanMessage(f"User: {msg}")]}
        except queue.Empty:
            thought = wander(state["short_persona_description"], hippocampus,
                              aff.mood.as_tuple(), pers, fast_chain, int(now_ts))
            if thought:
                return {"status": "active",
                        "messages": [HumanMessage(
                            f"Event: {wait}s of silence. A thought drifts: {thought}"
                        )]}
            return {"status": "active",
                    "messages": [HumanMessage(f"Event: {wait}s elapsed. No reply yet.")]}

    # --- sleep -----------------------------------------------------------
    def sleep(state):
        pers, aff, _, _ = _rehydrate(state)
        now_ts = time.time()
        msgs = state["messages"]
        if len(msgs) >= 4:
            episodes = []
            for i in range(0, len(msgs) - 1, 2):
                if i + 1 >= len(msgs): break
                h = msgs[i].content
                a = msgs[i + 1].content
                if h and a:
                    episodes.append(f"Human: {h}\\n{state['persona']}: {a}")
            consolidate(episodes, hippocampus, aff.mood.as_tuple(),
                        cloud_chain, int(now_ts))
        print(f"\\n[{state['persona']} is now dormant. Goodbye.]")
        return {"status": "dormant"}

    def route_end(state) -> Literal["thalamus", "sleep"]:
        return "sleep" if state.get("status") == "dormant" else "thalamus"

    return {
        "init_node": init_node, "thalamus": thalamus, "amygdala": amygdala,
        "hippocampus": hippocampus_node, "ofc_appraise": ofc_appraise,
        "motor_fast": motor_fast, "motor_full": motor_full,
        "encode_episode": encode_episode, "activate": activate, "sleep": sleep,
        "route_motor": route_motor, "route_end": route_end,
    }
'''


# =========================================================================
# graph/build.py
# =========================================================================
FILES["graph/build.py"] = '''from langgraph.graph import StateGraph, START, END
from graph.state import PsycheState


def build_graph(nodes: dict, checkpointer):
    g = StateGraph(PsycheState)
    for name in ["init_node", "thalamus", "amygdala", "hippocampus",
                 "ofc_appraise", "motor_fast", "motor_full",
                 "encode_episode", "activate", "sleep"]:
        g.add_node(name, nodes[name])

    g.add_edge(START, "init_node")
    g.add_edge("init_node", "thalamus")
    g.add_edge("thalamus", "amygdala")
    g.add_edge("amygdala", "hippocampus")
    g.add_edge("hippocampus", "ofc_appraise")
    g.add_conditional_edges("ofc_appraise", nodes["route_motor"])
    g.add_edge("motor_fast", "encode_episode")
    g.add_edge("motor_full", "encode_episode")
    g.add_edge("encode_episode", "activate")
    g.add_conditional_edges("activate", nodes["route_end"])
    g.add_edge("sleep", END)

    return g.compile(checkpointer=checkpointer)
'''


# =========================================================================
# llm_models.py
# =========================================================================
FILES["llm_models.py"] = '''"""
Build main / fast / cloud LLM chains.

Tries Ollama first for local models; falls back to cloud if unavailable.
"""
import os
from langchain_core.output_parsers import StrOutputParser


def _build_cloud():
    # Prefer OpenRouter if key present; otherwise fall back to OpenAI.
    if os.getenv("OPENROUTER_API_KEY"):
        try:
            from langchain_openrouter import ChatOpenRouter
            model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v3.2")
            return ChatOpenRouter(model=model, temperature=0.7, top_p=0.7)
        except ImportError:
            # fall through to OpenAI
            pass
        # Some distros expose OpenRouter via OpenAI-compatible base URL:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v3.2"),
                temperature=0.7, top_p=0.7,
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        except Exception:
            pass
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                       temperature=0.7, top_p=0.7)


def build_llm_chains():
    parser = StrOutputParser()
    cloud = _build_cloud()

    try:
        from langchain_ollama import ChatOllama
        main = ChatOllama(
            model=os.getenv("OLLAMA_MAIN",
                             "hf.co/mradermacher/Gemma-4-31B-Cognitive-Unshackled-i1-GGUF:Q4_K_M"),
            temperature=0.8, top_p=0.9,
        )
        fast = ChatOllama(
            model=os.getenv("OLLAMA_FAST",
                             "hf.co/TrevorJS/gemma-4-E4B-it-uncensored-GGUF:Q4_K_M"),
            temperature=0.6, top_p=0.9,
        )
        _ = fast.invoke("ok")   # health check
    except Exception as e:
        print(f"[llm] Ollama unavailable ({e}); using cloud for everything.")
        main = fast = cloud

    return {
        "main_chain":  main  | parser,
        "fast_chain":  fast  | parser,
        "cloud_chain": cloud | parser,
    }
'''


# =========================================================================
# utils.py
# =========================================================================
FILES["utils.py"] = '''import json
import queue
import threading


def read_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_config(cfg, path="config.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def make_input_queue() -> queue.Queue:
    q = queue.Queue()

    def _reader():
        while True:
            try:
                line = input()
            except EOFError:
                break
            q.put(line)
            if line.strip().lower() in ("/quit", "/exit", "end"):
                break

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return q
'''


# =========================================================================
# psyche.ipynb  (generated as a proper notebook JSON)
# =========================================================================
def _make_notebook():
    import json
    cells = []

    def code_cell(src: str):
        cells.append({
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": src.splitlines(keepends=True),
        })

    def md_cell(src: str):
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": src.splitlines(keepends=True),
        })

    md_cell("# Psyche — Run Notebook\n\n"
            "Run each cell in order. Type messages in the input prompt in Cell 5.\n"
            "Type `/quit` to end the session cleanly.\n")

    code_cell('''import os, time, sqlite3
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv, find_dotenv

from pinecone import Pinecone
from langgraph.checkpoint.sqlite import SqliteSaver

from mind.personality import Personality
from mind.affect      import AffectState, PAD
from mind.needs       import Drives
from mind.tom         import UserModel
from mind.memory      import Hippocampus

from graph.nodes      import build_nodes
from graph.build      import build_graph
from llm_models       import build_llm_chains
from utils            import read_config, write_config, make_input_queue

load_dotenv(find_dotenv(), override=True)
''')

    code_cell('''pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("INDEX_NAME", "psyche-memory")

if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={"model": "llama-text-embed-v2", "field_map": {"text": "chunk_text"}},
    )
index = pc.Index(index_name)

chains = build_llm_chains()
print("LLMs ready.")
''')

    code_cell('''cfg = read_config("config.json")
persona_key = cfg["chosen_persona"]
p = cfg[persona_key]

utc_offset = int(os.getenv("UTC_OFFSET", "-5"))
now_iso = datetime.now(timezone(timedelta(hours=utc_offset))).isoformat()

cfg[persona_key]["latest_date"] = now_iso
write_config(cfg)

personality = Personality.from_dict(p["personality_ocean"])
baseline = PAD(**p["baseline_pad"])
affect = AffectState()
affect.baseline = baseline
affect.mood     = PAD(**p["baseline_pad"])
drives = Drives(levels=dict(p["initial_drives"]))

input_state = {
    "messages": [],
    "persona": persona_key,
    "persona_description": p["persona_description"],
    "short_persona_description": p["short_persona_description"],
    "values": p.get("values", []),
    "personality": personality.to_dict(),
    "affect": affect.to_dict(),
    "drives": drives.to_dict(),
    "user_model": UserModel().to_dict(),
    "goals": [],
    "working_memory": [],
    "appraisal": {},
    "memories": [],
    "summary": "",
    "emotions_trace": [],
    "utc_offset": utc_offset,
    "latest_response": None,
    "status": "active",
    "last_tick_ts": time.time(),
}
print(f"Persona: {persona_key}   |   Thread: {now_iso}")
''')

    code_cell('''hippocampus = Hippocampus(
    index, persona_key,
    memory_length=int(os.getenv("MEMORY_LENGTH", "200")),
)

input_queue = make_input_queue()

nodes = build_nodes(
    hippocampus=hippocampus,
    fast_chain  = chains["fast_chain"],
    cloud_chain = chains["cloud_chain"],
    main_chain  = chains["main_chain"],
    input_queue = input_queue,
)

db = sqlite3.connect("psyche.db", check_same_thread=False)
checkpointer = SqliteSaver(db)
app = build_graph(nodes, checkpointer)
print("Graph compiled.")
''')

    code_cell('''config = {"configurable": {"thread_id": now_iso}, "recursion_limit": 500}

print("=" * 60)
print(f"Psyche is waking up as {persona_key}.")
print("Type your messages and press Enter. Type /quit to end.")
print("=" * 60)

final = app.invoke(input_state, config=config)

print("\\nFinal mood:", AffectState.from_dict(final["affect"]).describe(time.time()))
print("Drives:",     Drives.from_dict(final["drives"]).describe())
''')

    code_cell('''state = app.get_state({"configurable": {"thread_id": now_iso}})
v = state.values
print("Personality:", v["personality"])
print("Affect:     ", AffectState.from_dict(v["affect"]).describe(time.time()))
print("Drives:     ", Drives.from_dict(v["drives"]).describe())
print("User model: ", UserModel.from_dict(v["user_model"]).describe())
print("Appraisal:  ", v.get("appraisal"))
''')

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(nb, indent=1)


FILES["psyche.ipynb"] = _make_notebook()


# =========================================================================
# Main
# =========================================================================
def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("psyche")
    target.mkdir(parents=True, exist_ok=True)
    print(f"Writing project to: {target.resolve()}")

    for rel_path, content in FILES.items():
        full = target / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        print(f"  wrote  {rel_path}")

    print("\nDone. Next steps:")
    print(f"  cd {target}")
    print( "  python -m venv .venv && source .venv/bin/activate   # or .venv\\Scripts\\activate on Windows")
    print( "  pip install -r requirements.txt")
    print( "  cp .env.example .env     # then edit .env with your keys")
    print( "  jupyter lab psyche.ipynb")


if __name__ == "__main__":
    main()