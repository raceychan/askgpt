FROM python:3.12 AS builder

# install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:${PATH}"

# Set the working directory in the Docker image
WORKDIR /app

# Copy the pixi files
COPY pixi.lock pixi.toml ./

# # Install dependencies using Pixi
RUN pixi install

# Copy only the src directory into the Docker image
COPY src ./src

# Set the command to run the application
CMD ["pixi", "run", "python", "-m", "src.server"]
