# AskGPT

- [AskGPT](#askgpt)
  - [Introduction](#introduction)
  - [Supported-platform](#supported-platform)
  - [Local Model Serving](#local-model-serving)
  - [Note](#note)
  - [Community](#community)
  - [Usage](#usage)
  - [Test](#test)
  - [Deployment](#deployment)
    - [single-node](#single-node)
  - [External-Dependencies](#external-dependencies)
  - [Features](#features)

## Introduction

AskGPT is a production-ready Dstirbuted, multi-Tenant ML-OPS platform that enables businesses to leverage cutting-edge language models like OpenAI's ChatGPT and various LLMs models. It's built with a robust multi-tenant architecture, powerful actor-based computational model, and a reactive, user-friendly interface.

## Supported-platform

All major cloud providers are supported, including AWS, GCP, and Azure. AskGPT is also compatible with local LLMs, such as Llama2.
but currently these are the ones we have tested, and ones you can call directly from the webapi.

| Supported Cloud Provider  |
| ------------------------- |
| OpenAI                    |
| Anthropic                 |

| Supported Local LLMs |
| ---------------------|
| Llama2               |

## Local Model Serving

Local model serving is supported using llama.cpp, due to the size restriction
you will need to download your model on your own and place them
in the `actors/src/models` fodler
corresponding apis will be defined in the `backend/src/app/api` directory, and call llm using ray.

## Note

Chat Completion is not async and not blocking, meaning that you can send multiple requests to the corresponding endpoints and expect streaming response concurrently from the server.

However, API throttling might apply depending on spec of each model, for remote model like openai chatgpt, you can increase the number of current request by adding more api-keys, askgpt will  manage api throttling for you.  

## Community

1. discord: [askgpt-discussion](https://discord.gg/D44Hz9pTMe)

## Usage

1. create your own `settings.toml` in the project root under `askgpt/src`

2. In your terminal:

```bash
make install
make server
```

## Test

```bash
make test
```

## Deployment

### single-node

single-node deployment can be done using docker-compose, multicode are well supported.
all-heavy workloads are handled by ray-core, which should be pre-deployed as a cluster in the production environment.

```bash
cd askgpt # project root
docker-compose up -d
```

## External-Dependencies

All external dependencies are plugable by design, client code are well-encapsulated to be easily extended with sub-class.

With that being said, our current choices of components are

| Component | Name |
| ------ | ------ |
| Message Queue | Apache Pulsar |
| Cache | Redis |
| SQL-database | Postgresql |
| Distributed actors | Ray-core |
| LLMS models | Huggingface Transformers |

## Features

1. Robust Multi-Tenancy: AskGPT is built with multi-tenancy at its core. Administrators can effortlessly share API access with sub-users, ensuring that each tenant's data and messages remain isolated and secure. This feature is ideal for businesses that require compartmentalized access for different departments or client accounts.

2. Separation of Computation and I/O: At the heart of our system is a highly extensible actor model, providing dedicated computational resources. This separation ensures efficient processing and responsiveness, even under heavy loads. Our design optimizes resource utilization, paving the way for a scalable and reliable service.

3. Support for Multiple Language Models: We embrace the diversity of AI language models. it is not only compatible with OpenAI's ChatGPT but also supports various LLMs models. This flexibility allows users to choose the model that best fits their specific needs and preferences.

4. Reactive and Responsive System: Designed to be highly responsive, it ensures a seamless and interactive user experience. The reactive architecture efficiently handles user requests and system events, ensuring quick and accurate responses.

5. Efficient User Session Management: We offer a sophisticated user session management system that maintains stateful interactions seamlessly. This feature enhances user experience by enabling personalized and context-aware interactions with the system.

6. High-Performance, Scalable Model Serving: Leveraging the actor model, our platform achieves high performance in distributed model serving. It's designed for scalability, ensuring consistent performance even as demand grows. This system is ideal for handling complex, large-scale AI workloads efficiently.

7. Multi-Dimensional API Throttling: Our platform implements nuanced API throttling, offering multiple dimensions of control, including global and API-key-specific limits. This feature allows for fine-grained management of resource utilization and ensures fair usage across all users.

8. Concurrency-First, Asynchronous Architecture: The system is built with a concurrency-first, async-first, and distributed-first approach, ensuring high responsiveness and reliability. This architecture is key to handling high-volume, parallel requests without compromising on performance.

9. CQRS for Comprehensive Audit Logs: Incorporating Command Query Responsibility Segregation (CQRS), our platform provides detailed audit logs, enhancing transparency and traceability. This is vital for monitoring system usage, troubleshooting, and complying with regulatory requirements.
