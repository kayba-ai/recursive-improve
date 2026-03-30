"""Harbor agent wrapper: injects custom CLAUDE.md into the container."""

import os
from pathlib import Path

from harbor.agents.installed.claude_code import ClaudeCode


class EvolveClaudeCode(ClaudeCode):
    """Claude Code agent with custom CLAUDE.md injection for /evolve."""

    @staticmethod
    def name() -> str:
        return "evolve-claude-code"

    async def install(self, environment) -> None:
        await super().install(environment)

        # Read CLAUDE.md from host (island worktree) and inject into container
        claudemd_path = os.environ.get("EVOLVE_CLAUDEMD", "CLAUDE.md")
        path = Path(claudemd_path)
        if not path.exists():
            return

        content = path.read_text(encoding="utf-8")
        # Write to both home dir and working dir so Claude Code finds it
        for target in ["~/CLAUDE.md", "./CLAUDE.md"]:
            await self.exec_as_agent(
                f"cat > {target} << 'EVOLVE_EOF'\n{content}\nEVOLVE_EOF"
            )
