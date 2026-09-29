# Safe coding/CTF sandbox architecture

For real Python/Java execution, do not use `subprocess` directly from Flask with unrestricted input.

Recommended production flow:
Browser -> API -> job queue -> isolated container/VM -> runner -> result
- No host filesystem access
- No privileged container
- Network disabled by default
- CPU/memory/time limits
- Read-only base image
- Ephemeral workspace
- Kill timed-out jobs
- Separate challenge network for intentionally vulnerable targets
- Log and rate-limit submissions

This keeps student practice separate from the web server and prevents a coding exercise from becoming
a path to the host machine.
