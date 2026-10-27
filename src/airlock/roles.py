"""Role resolution: content magic, then globs from `rules/roles.toml`, then extension fallback.

Task 2.4 (ARCHITECTURE.md 6.2). The glob matcher is internal because `fnmatch` lets a lone
`*` cross directory boundaries. `\0asm` gives `wasm`; ELF, PE and Mach-O magics give
`native-binary`, regardless of extension.
"""
