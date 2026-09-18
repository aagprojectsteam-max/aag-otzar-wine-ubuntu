# Contributing

Keep changes narrow and evidence-driven.

Before submitting a change:
1. run scripts/public-scan.sh;
2. run Python and shell syntax checks;
3. build the input filter from source;
4. state which layer the change affects;
5. document automated versus physical validation;
6. do not add vendor binaries, databases, content, Wine prefixes, or licensing material.

Compatibility patches must abort on ambiguous anchors rather than guessing.
