# apply/ — writing fixes back to Figma

**Status: not decided yet.** This does not block anything else.

Figma's REST API is **read-only for design content**, so C3's ranked fixes cannot be
applied to the canvas over REST. Options to choose from as a team:

| Option | How it works | Effort |
|---|---|---|
| **A. Report only** | Keep the Markdown report from the app as the deliverable. | None |
| **B. Figma comments** | Post each fix as a comment pinned to its node via `POST /v1/files/:key/comments` (`client_meta.node_id`). Needs a token with the `file_comments:write` scope. Designers see the fixes in Figma, nothing is edited. | Low |
| **C. Figma plugin bridge** | Export C3's fix list as JSON (node IDs + fix); a small TypeScript Figma plugin reads it and highlights or applies changes with the Plugin API. | Medium–high |

Whatever is chosen, the input is the same: `Recommendation.fixes` from
`components/recommendation/recommend.py` (each fix carries `node_ids`, `factor`, `fix`).
