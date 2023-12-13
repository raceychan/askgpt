# Distributed GPT Client

## Introducing AskGPT

Multi-Tenant Chatbot Platform
AskGPT is a Multi-Tenant Chatbot Platform, an advanced solution designed to empower businesses with scalable and secure access to cutting-edge language models like OpenAI's ChatGPT and various LLaMA models. it stands out with its robust multi-tenant architecture, powerful actor-based computational model, and a reactive, user-friendly interface.

Key Features
Robust Multi-Tenancy: AskGPT is built with multi-tenancy at its core. Administrators can effortlessly share API access with sub-users, ensuring that each tenant's data and messages remain isolated and secure. This feature is ideal for businesses that require compartmentalized access for different departments or client accounts.

Separation of Computation and I/O: At the heart of our system is a highly extensible actor model, providing dedicated computational resources. This separation ensures efficient processing and responsiveness, even under heavy loads. Our design optimizes resource utilization, paving the way for a scalable and reliable service.

Support for Multiple Language Models: We embrace the diversity of AI language models. it is not only compatible with OpenAI's ChatGPT but also supports various LLaMA models. This flexibility allows users to choose the model that best fits their specific needs and preferences.

Reactive and Responsive System: Designed to be highly responsive, it ensures a seamless and interactive user experience. The reactive architecture efficiently handles user requests and system events, ensuring quick and accurate responses.

## Usage

1. create your own `settings.toml` in the project root under `askgpt/src`

2. In your terminal:

```python
make install
make server
```
