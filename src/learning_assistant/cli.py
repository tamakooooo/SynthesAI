"""
Learning Assistant CLI Entry Point.

This module provides the main CLI application using Typer.
"""

import typer
from rich.console import Console

# Create Typer app
app = typer.Typer(
    name="learning-assistant",
    help="A modular, plugin-based AI learning assistant CLI tool",
    add_completion=False,
)

# Create Rich console for beautiful output
console = Console()


@app.command()
def version() -> None:
    """Show the version of Learning Assistant."""
    from learning_assistant import __version__
    console.print(f"[bold green]Learning Assistant[/bold green] version: {__version__}")


@app.command()
def setup() -> None:
    """Interactive setup wizard for first-time configuration."""
    console.print("[bold blue]Welcome to Learning Assistant Setup Wizard![/bold blue]")

    # Check Python version
    import sys
    console.print(f"\n[yellow]Python Version:[/yellow] {sys.version}")

    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[green]✓[/green] FFmpeg is installed")
        else:
            console.print("[red]✗[/red] FFmpeg is not installed")
    except FileNotFoundError:
        console.print("[red]✗[/red] FFmpeg is not installed (required for video processing)")

    # Check API keys
    import os
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
    }

    console.print("\n[yellow]API Keys:[/yellow]")
    for key_name, key_value in api_keys.items():
        if key_value:
            console.print(f"[green]✓[/green] {key_name} is set")
        else:
            console.print(f"[red]✗[/red] {key_name} is not set")

    console.print("\n[bold blue]Setup complete![/bold blue]")
    console.print("[yellow]Next steps:[/yellow]")
    console.print("  1. Install FFmpeg if needed: https://ffmpeg.org/download.html")
    console.print("  2. Set API keys in environment variables")
    console.print("  3. Run: la video <video_url> to test")


@app.command()
def list_plugins() -> None:
    """List all available plugins (modules and adapters)."""
    console.print("[bold blue]Available Plugins:[/bold blue]")
    console.print("\n[yellow]Modules:[/yellow]")
    console.print("  • video_summary (enabled)")
    console.print("  • link_learning (disabled)")
    console.print("  • vocabulary (disabled)")
    console.print("\n[yellow]Adapters:[/yellow]")
    console.print("  • feishu (disabled)")
    console.print("  • siyuan (disabled)")
    console.print("  • obsidian (disabled)")
    console.print("\n[yellow]Note:[/yellow] Use 'la video' to test video summary module")


@app.command()
def history() -> None:
    """Show learning history."""
    console.print("[bold blue]Learning History:[/bold blue]")
    console.print("[yellow]No history records found[/yellow]")
    console.print("[dim]History tracking will be enabled after processing first video[/dim]")


# Placeholder for module commands (will be dynamically registered by PluginManager)
@app.command()
def video(
    url: str = typer.Argument(..., help="Video URL to process"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format (markdown, json, pdf)"),
) -> None:
    """
    Summarize video content (MVP module).

    Example: la video https://www.bilibili.com/video/BV123
    """
    console.print(f"[bold blue]Processing video:[/bold blue] {url}")
    console.print("[yellow]Video summary module is under development[/yellow]")
    console.print("[dim]Module will be implemented in Week 3-4[/dim]")


if __name__ == "__main__":
    app()