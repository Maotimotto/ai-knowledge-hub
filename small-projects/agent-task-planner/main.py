"""Agent Task Planner - CLI tool for goal decomposition and planning."""

import json
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()


def display_plan(plan: dict) -> None:
    """Display a structured plan using Rich formatting."""
    console.print(Panel(f"[bold blue]Goal:[/bold blue] {plan.get('goal', 'N/A')}", title="🎯 Task Plan"))

    tasks = plan.get("tasks", [])
    if not tasks:
        console.print("[yellow]No structured tasks generated.[/yellow]")
        if "raw_response" in plan:
            console.print(Panel(plan["raw_response"], title="Agent Response"))
        return

    table = Table(title="📋 Tasks", show_lines=True)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Title", style="green", width=30)
    table.add_column("Priority", style="yellow", width=10)
    table.add_column("Hours", style="magenta", width=8)
    table.add_column("Description", width=50)

    priority_colors = {"high": "red", "medium": "yellow", "low": "green"}
    for task in tasks:
        pri = task.get("priority", "medium")
        color = priority_colors.get(pri, "white")
        table.add_row(
            str(task.get("id", "?")),
            task.get("title", ""),
            f"[{color}]{pri}[/{color}]",
            str(task.get("estimated_hours", "?")),
            task.get("description", "")[:50],
        )

    console.print(table)

    # Timeline and resources
    if plan.get("timeline"):
        console.print(f"\n[bold]📅 Timeline:[/bold] {plan['timeline']}")
    if plan.get("resources_needed"):
        console.print(f"[bold]🔧 Resources:[/bold] {', '.join(plan['resources_needed'])}")
    if plan.get("risks"):
        console.print(f"[bold]⚠️  Risks:[/bold] {', '.join(plan['risks'])}")

    total_hours = sum(t.get("estimated_hours", 0) for t in tasks)
    console.print(f"\n[bold green]Total estimated effort: {total_hours} hours[/bold green]")


def main():
    """Main CLI entry point."""
    console.print(Panel("[bold]Agent Task Planner[/bold]\nPowered by ReAct-style planning", title="🤖"))

    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    else:
        console.print("[yellow]Usage: python main.py 'your goal here'[/yellow]")
        console.print("\nExample goals:")
        console.print("  • 'Plan a marketing campaign for AI tool'")
        console.print("  • 'Build a mobile app for fitness tracking'")
        console.print("  • 'Launch a SaaS product in 3 months'")
        goal = console.input("\n[bold cyan]Enter your goal:[/bold cyan] ")

    if not goal.strip():
        console.print("[red]No goal provided. Exiting.[/red]")
        sys.exit(1)

    console.print(f"\n[dim]Planning: {goal}[/dim]")
    console.print("[dim]Using ReAct agent with tools...[/dim]\n")

    from planner import PlanningAgent
    agent = PlanningAgent()
    plan = agent.plan(goal)

    console.print()
    display_plan(plan)

    # Save plan to file
    output_file = "plan_output.json"
    with open(output_file, "w") as f:
        json.dump(plan, f, indent=2)
    console.print(f"\n[dim]Plan saved to {output_file}[/dim]")


if __name__ == "__main__":
    main()
