"""
# Dependency-Wrapper
## Thin wrapperss around third-party libs, do not contain any business logic,
they are good for:
- provide a more convenient interface for layer 2
- implement open-close principle, if we want to change the third-party library,we can simply extend the wrap class 
- used as test doubles, we can always create a fake, in-memory version of the wrap class, like in-memory redis, in-memory database, etc.
- used as a breaking-change buffer, when we upgrade the third-party library, we can make the wrap class compatible with the old version, without touching layers above it.


This is not part of the onion architecture or ddd

TODO: we should consider make this a private repo
"""
