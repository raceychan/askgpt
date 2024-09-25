FROM python:3.12 AS python-base

FROM python-base as builder-base
# install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash

ENV PIXI_HOME="/root/.pixi"
ENV PATH="$PIXI_HOME/bin:${PATH}"

# Set the working directory in the Docker image
WORKDIR /app

# Copy the pixi files
# COPY pixi.lock pixi.toml ./
COPY pixi.toml ./

# # Install dependencies using Pixi
RUN pixi install

COPY askgpt ./askgpt

ENTRYPOINT ["pixi", "run", "uvicorn"]
CMD ["askgpt.app.app:app_factory"]