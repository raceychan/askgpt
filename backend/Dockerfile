FROM python:3.12-slim-bullseye 

RUN apt-get update && apt-get install -y \
    curl
# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PIXI_HOME="/root/.pixi"
ENV PATH="$PIXI_HOME/bin:${PATH}"

# Set the working directory in the Docker image
WORKDIR /app

# Pip uses pyproject.toml to install dependencies
COPY pixi.lock pyproject.toml ./

# Install dependencies using pixi, caching the result in a volume
RUN --mount=type=cache,target=/root/.pixi/cache \
    pixi install

# Install dependencies using pip
RUN pixi install

# Grant privilages to pixi
RUN chmod +x .pixi

# create dev database file
RUN if [ "$RUNTIME_ENV" = "dev" ]; then touch dev.db; fi

# Copy the project first so that dependencies can be installed
COPY askgpt ./askgpt
EXPOSE 5000
ENTRYPOINT ["pixi", "run", "-e", "dev"]
CMD ["uvicorn", "askgpt.api.app:app_factory"]