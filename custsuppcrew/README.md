# Custsuppcrew Crew

Welcome to the Custsuppcrew Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/custsuppcrew/config/agents.yaml` to define your agents
- Modify `src/custsuppcrew/config/tasks.yaml` to define your tasks
- Modify `src/custsuppcrew/crew.py` to add your own logic, tools and specific args
- Modify `src/custsuppcrew/main.py` to add custom inputs for your agents and tasks

## Running the Project

Use **this project’s** `.venv` (not the parent `AAMD-main/.venv`). If your prompt shows a venv from another directory, deactivate it first.

```bash
cd /path/to/custsuppcrew
deactivate 2>/dev/null || true
unset VIRTUAL_ENV
source .venv/bin/activate
crewai run
```

Or use the launcher (same fix, one command):

```bash
./run.sh
```

**Do not** pass `--active` to `crewai` — that flag belongs to `uv`, and `crewai run` will fail with `No such option '--active'`.

If you see:
`VIRTUAL_ENV=.../AAMD-main/.venv does not match the project environment path .venv`
your shell still has the parent venv active; run the `deactivate` / `unset VIRTUAL_ENV` / `source .venv/bin/activate` steps above.

This command initializes the custsuppcrew Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The custsuppcrew Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the Custsuppcrew Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
