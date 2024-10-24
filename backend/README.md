# AskGPT-BackEnd

## TechStack

- FastAPI
- SQLAlchemy
- Redis
- Postgres
- Alembic

## Architecture

### service classes vs functions

- service classes:
  - Pros:
    - clear relationship between services
    - as dependency goes, methods are eaiser to write
    - might group classes into a module, yet each class is self-contained.

  - Cons:
    - not every method uses all the dependencies, but because of the class, the dependencies are instantiated anyway.
    - carry state, but requests are stateless.