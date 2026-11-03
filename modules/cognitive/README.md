# Cognitive modules

This package is the application-side home for cognitive-system prototypes.
Keep components independently testable and connect them through explicit,
structured inputs rather than importing another component's internal state.

## Draft structure

```text
modules/cognitive/
├── information_space/   # Current: score an evidence ecology
├── mindwaves/           # Track ecology fluctuations and attention changes
├── veganator/           # Planned: evaluate candidate ideas and constraints
└── reality_feedback/    # Planned: compare predictions with observations
```

The Information Ecology Engine is the first implementation. It accepts
structured signals and returns 11 descriptive metrics. Scores are bounded
between 0 and 1; they are indicators, not claims of human-like understanding.
Its coherence metric is lexical overlap, not semantic coherence.

## Information Ecology dimensions

| Metric | Interpretation |
|---|---|
| `signal_volume` | Signal count with a saturating scale |
| `source_diversity` | Fraction of signals from distinct sources |
| `coherence` | Mean pairwise lexical Jaccard similarity |
| `novelty` | Mean caller-supplied novelty |
| `uncertainty` | Mean of `1 - confidence` |
| `relevance` | Mean caller-supplied relevance |
| `attention` | Mean caller-supplied attention |
| `memory` | Mean caller-supplied retention |
| `prediction_error` | Mean caller-supplied prediction error |
| `goal_alignment` | Mean caller-supplied goal alignment |
| `utility` | Mean caller-supplied utility |

Empty input produces zero for each metric. The engine does not combine these
dimensions into an overall score, since high values do not uniformly indicate
a better outcome.

MindWaves consumes successive ecology snapshots. It reports mean absolute
metric change (`fluctuation`), the current attention score, its change from
the previous snapshot, and a bounded history for live visualization. The first
snapshot establishes a baseline with zero fluctuation.

`CognitiveRuntime` isolates the latest snapshot and MindWaves tracker by
session ID. Investigation workers use `investigation:<id>`; REST clients may
provide a reusable `session_id` or let the API create one. Runtime contexts are
kept in an in-memory LRU capped at 128 sessions, so state does not persist
across process restarts and an evicted session starts empty if recreated.
In-flight reads and evaluations pin a context against eviction; if all slots
are pinned, creation of a new context waits. Contexts are process-local;
multi-worker deployments require shared storage. Session IDs scope state but do
not provide authorization.

During investigations, the cockpit uses completed agent output as signal
content, assigns the active agent an attention value of `1` and other completed
agents `0`, and leaves the other signal attributes at their neutral defaults.
Use the evaluation endpoint to provide explicit values for those attributes.
