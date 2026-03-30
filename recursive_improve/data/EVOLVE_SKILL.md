---
name: evolve
description: >
  Evolutionary search for agent improvement using Mind Evolution. Manages
  multiple parallel improvement islands via git worktrees, with selection
  and cross-pollination. Invoke with /evolve, "evolve my agent",
  "run evolutionary search", "parallel improvement".
---

# /evolve — Evolutionary Agent Improvement

Parallel improvement search. Multiple islands (git worktrees) explore different
improvement strategies independently. After each generation, the best island's
ideas cross-pollinate to others.

---

## Step 1: Configure (MANDATORY — do not skip)

### If `program.md` exists

Read it. If no `## Evolution` section, add defaults:

```markdown
## Evolution
- n_islands: 4
- n_generations: 10
```

Present to user and confirm. Update `program.md` with any changes.

### If `program.md` does not exist

Follow the same flow as `/ratchet` Step 1, plus ask for evolution params.

**Do NOT proceed until the user confirms.**

---

## Step 2: Initialize

```bash
recursive-improve evolve init --config program.md
```

Parse JSON output. Note `session_id`, `base_ref`, and island paths.
Store the **repo root** as an absolute path — you'll need it for config paths.

---

## Step 3: Evolution Loop

Track `generation` starting at 1.

### 3a. Improve each island

For each island 0 to N-1:

1. **cd into the island's worktree:**
   ```bash
   cd .ri-islands/island-{id}
   ```

2. **Cross-pollination (generation > 1 only):**

   **Diversity island:** If `island_id == generation % n_islands`, skip
   cross-pollination entirely. Improve independently to preserve diversity.

   **All other islands:** Read ALL other islands' diffs with their scores:
   ```bash
   # For each other island i (skip your own):
   echo "=== Island {i} (score: {score_i}) ==="
   git -C {repo_root}/.ri-islands/island-{i} diff {base_ref}...HEAD
   ```

   Your primary references for this round:
   - **Primary (exploit):** Island {best_id} (score {best_score}) — the
     current leader. Deeply analyze what it changed and why it works.
   - **Explore:** Island {random_other_id} (score {score}) — randomly
     picked from the remaining islands. Study it for alternative ideas,
     unconventional approaches, or hidden gems even if its overall score
     is low.

   Deeply compare these two. The primary shows what works. The explorer
   might have ideas worth incorporating that the leader missed. The
   remaining diffs are available for additional context if needed.

3. **Run the improvement pipeline:**
   Run `/recursive-improve` (stages 0–7) in the island's worktree with auto-approve.
   Apply fixes directly to the working tree. Skip stages 0-2 if domain context exists.

4. **Run the agent** (if configured):
   ```bash
   rm -f {traces_dir}/*.json
   {agent_run_command}
   ```

5. **Commit changes:**
   ```bash
   git add -A && git commit -m "evolve: gen {generation} island {id}"
   ```

6. **Evaluate:**
   **IMPORTANT:** Use absolute path to `program.md` since you're inside a worktree.
   ```bash
   recursive-improve ratchet eval --config {repo_root}/program.md
   ```
   Parse JSON output. Get the `score` field.

7. **Record the score:**
   ```bash
   recursive-improve evolve update --island {id} --score {score} --generation {generation} --config {repo_root}/program.md
   ```

### 3b. Check progress

```bash
recursive-improve evolve status --config {repo_root}/program.md
```

Parse JSON. Note `best_island`, `best_score`, and `converged`.

If `converged` is true or `generation >= n_generations`: proceed to Step 4.

Otherwise: increment `generation`, go to 3a.

---

## Step 4: Finalize

1. Read status to get the best island:
   ```bash
   recursive-improve evolve status --config program.md
   ```

2. Create a result branch from the best island:
   ```bash
   git branch ri/evolve-{session_id}-result ri/evolve-{session_id}-island-{best_island}
   ```

3. Clean up worktrees:
   ```bash
   recursive-improve evolve cleanup --config program.md
   ```

4. Checkout the result branch:
   ```bash
   git checkout ri/evolve-{session_id}-result
   ```

---

## Step 5: Summary

Tell the user:
- **Result branch:** `ri/evolve-{session_id}-result`
- **Best score:** {score} from island {best_island}
- **Generations:** {n}
- **Review:** `git diff main...ri/evolve-{session_id}-result`
- **Merge:** `git merge ri/evolve-{session_id}-result` or open a PR
- **Discard:** `git branch -D ri/evolve-{session_id}-result`

---

## Rules

- Each island is fully isolated — work inside its worktree directory
- Never modify the main branch during evolution
- Do NOT modify trace files
- **Always use absolute paths** for `--config` when inside a worktree
- Cross-pollination: show all diffs but deeply reference the best + one random island
- One island per generation skips cross-pollination (diversity preservation: `island_id == generation % n_islands`)
- Keep fixes small and targeted — smaller changes are easier to compare across islands
- If an island's improvement fails, skip it and continue to the next
- Always commit before evaluating so the diff is available for cross-pollination
- Always call `evolve update` after evaluation to persist scores
