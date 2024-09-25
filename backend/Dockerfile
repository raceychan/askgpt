FROM python:3.12 AS python-base

FROM python-base as builder-base

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PIXI_HOME="/root/.pixi"
ENV PATH="$PIXI_HOME/bin:${PATH}"

# Set the working directory in the Docker image
WORKDIR /app

# Pip uses pyproject.toml to install dependencies
COPY pyproject.toml ./

# Install dependencies using pip
RUN pixi install 

RUN chmod +x .pixi

# Copy the project first so that dependencies can be installed
COPY askgpt ./askgpt

ENTRYPOINT ["pixi", "run", "uvicorn"]
CMD ["askgpt.app.app:app_factory"]