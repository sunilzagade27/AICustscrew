from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from custsuppcrew.llm_config import investigation_llm
from custsuppcrew.tools.read_only_tools import bind_specialist_tools, validate_bound_tools


@CrewBase
class Custsuppcrew:
    """SAD MVP SRE investigation crew (supervisor + four specialists)."""

    agents: list[BaseAgent]
    tasks: list[Task]

    def _specialist_tools(self) -> dict[str, list]:
        if not hasattr(self, "_tools_cache"):
            bound = bind_specialist_tools()
            validate_bound_tools(bound)
            self._tools_cache = bound
        return self._tools_cache

    def _investigation_llm(self):
        if not hasattr(self, "_llm_cache"):
            self._llm_cache = investigation_llm()
        return self._llm_cache

    @agent
    def supervisor(self) -> Agent:
        return Agent(
            config=self.agents_config["supervisor"],  # type: ignore[index]
            tools=self._specialist_tools()["supervisor"],
            llm=self._investigation_llm(),
            verbose=True,
        )

    @agent
    def kubernetes_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["kubernetes_specialist"],  # type: ignore[index]
            tools=self._specialist_tools()["kubernetes_specialist"],
            llm=self._investigation_llm(),
            verbose=True,
        )

    @agent
    def logs_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["logs_specialist"],  # type: ignore[index]
            tools=self._specialist_tools()["logs_specialist"],
            llm=self._investigation_llm(),
            verbose=True,
        )

    @agent
    def metrics_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["metrics_specialist"],  # type: ignore[index]
            tools=self._specialist_tools()["metrics_specialist"],
            llm=self._investigation_llm(),
            verbose=True,
        )

    @agent
    def runbooks_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["runbooks_specialist"],  # type: ignore[index]
            tools=self._specialist_tools()["runbooks_specialist"],
            llm=self._investigation_llm(),
            verbose=True,
        )

    @task
    def task_plan(self) -> Task:
        return Task(
            config=self.tasks_config["task_plan"],  # type: ignore[index]
        )

    @task
    def task_kubernetes(self) -> Task:
        return Task(
            config=self.tasks_config["task_kubernetes"],  # type: ignore[index]
        )

    @task
    def task_logs(self) -> Task:
        return Task(
            config=self.tasks_config["task_logs"],  # type: ignore[index]
        )

    @task
    def task_metrics(self) -> Task:
        return Task(
            config=self.tasks_config["task_metrics"],  # type: ignore[index]
        )

    @task
    def task_runbooks(self) -> Task:
        return Task(
            config=self.tasks_config["task_runbooks"],  # type: ignore[index]
        )

    @task
    def task_aggregate(self) -> Task:
        return Task(
            config=self.tasks_config["task_aggregate"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Sequential investigation crew with read-only stub tools."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            max_rpm=10,
        )
