---
name: p2p-chain
description: >-
  Run an explicit P2P chain of named real subagents in the requested order. Use when the
  user invokes $p2p-chain and supplies roles such as IRIS, TECTON, AXIOM, VECTOR, DATOS,
  ANON, ARCHITECTON, or HELIOS.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P Agent Chain

Parse only the eight recognized role names. Spawn one distinct real thread per
selected role when subagents are available and delegation was requested. Pass
distilled conclusions between roles, wait for the chain, and disclose the real
thread status. If real agents are unavailable, stop or offer a clearly labeled
single-agent alternative; never simulate multiple agents silently.
