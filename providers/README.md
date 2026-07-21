# Providers

This directory is intentionally empty of implementations.

A provider is just a callable `(prompt: str) -> str`. Wire your own — an HTTP
client, an SDK call, a local model — and pass it to `Provider(name, call)`.

Keep credentials in your environment, never in code. This project ships no keys,
no endpoints, and no routing logic, by design: the moment a repository carries a
credential "just for testing", it is one fork away from being public. See
lesson 01 in agent-ops-doctrines.
