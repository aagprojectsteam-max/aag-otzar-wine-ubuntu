# Security and Privacy

Do not commit user databases, licensed content, serials, API keys, tokens, private Wine prefixes, or vendor binaries.

The host input bridge is designed to read only modifier-key state snapshots, not the typed character stream.

Content should remain mounted read-only. Writable state belongs in a separate DATA directory.

Before publishing changes, run scripts/public-scan.sh and manually review the staged diff.
