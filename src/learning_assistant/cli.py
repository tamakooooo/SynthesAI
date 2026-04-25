"""
SynthesAI CLI Entry Point.

SynthesAI - Synthesize Knowledge with AI Intelligence
"""

import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from learning_assistant import __version__
from learning_assistant.auth import AuthManager
from learning_assistant.core.config_manager import ConfigManager
from learning_assistant.core.event_bus import EventBus
from learning_assistant.core.plugin_manager import PluginManager

# Create Typer app
app = typer.Typer(
    name="synthesai",
    help="SynthesAI - Synthesize Knowledge with AI Intelligence. AI-powered learning assistant for video summaries, knowledge cards, and vocabulary extraction",
    add_completion=False,
)

# Create auth command group
auth_app = typer.Typer(name="auth", help="Platform authentication management")
app.add_typer(auth_app, name="auth")

# Create Rich console for beautiful output
console = Console()


class AppState:
    """Global state for CLI application."""

    config_manager: ConfigManager | None = None
    event_bus: EventBus | None = None
    plugin_manager: PluginManager | None = None
    auth_manager: AuthManager | None = None

    def initialize(self, config_dir: Path) -> None:
        """Initialize core components."""
        # Initialize ConfigManager
        self.config_manager = ConfigManager(config_dir=config_dir)
        self.config_manager.load_all()

        # Initialize EventBus
        self.event_bus = EventBus()

        # Initialize PluginManager with plugin directories
        plugin_dirs = [
            config_dir.parent / "src" / "learning_assistant" / "modules",
            config_dir.parent / "src" / "learning_assistant" / "adapters",
            Path("plugins"),
        ]
        self.plugin_manager = PluginManager(plugin_dirs=plugin_dirs)

        # Discover plugins
        self.plugin_manager.discover_plugins()

        # Load all discovered plugins
        for plugin_name in self.plugin_manager.plugins.keys():
            self.plugin_manager.load_plugin(plugin_name)

        # Initialize loaded plugins with config and event_bus
        modules_config = (
            self.config_manager.modules_model.model_dump()
            if self.config_manager.modules_model
            else {}
        )
        adapters_config = (
            self.config_manager.adapters_model.model_dump()
            if self.config_manager.adapters_model
            else {}
        )
        adapter_subscriptions = adapters_config.get("event_bus", {}).get("subscriptions", {})
        plugin_config = modules_config.copy()
        for adapter_name, adapter_config in adapters_config.items():
            if adapter_name == "event_bus":
                continue
            adapter_payload = dict(adapter_config)
            adapter_payload["subscriptions"] = adapter_subscriptions.get(adapter_name, [])
            plugin_config[adapter_name] = adapter_payload
        self.plugin_manager.initialize_all(
            config=plugin_config, event_bus=self.event_bus
        )

        # Register plugin commands dynamically
        self._register_plugin_commands()

        # Initialize AuthManager
        modules_config = modules_config if self.config_manager.modules_model else {}
        video_summary_config = modules_config.get("video_summary", {})
        auth_config = video_summary_config.get("config", {}).get("auth", {})
        self.auth_manager = AuthManager(config=auth_config)

    def _register_plugin_commands(self) -> None:
        """Register plugin commands dynamically to CLI app."""
        if not self.plugin_manager:
            return

        # Iterate through loaded plugins
        for plugin_name, plugin_metadata in self.plugin_manager.loaded_plugins.items():
            # Check if plugin defines commands
            if not hasattr(plugin_metadata, "commands"):
                continue

            commands = plugin_metadata.commands
            if not commands:
                continue

            # Register each command
            for command_name, command_info in commands.items():
                # Create a wrapper function for the command
                # Use default arguments to capture loop variables
                def command_wrapper(
                    pn: str = plugin_name,
                    cn: str = command_name,
                    ci: dict[str, Any] = command_info,
                ) -> None:
                    console.print(f"[blue]Executing {pn}/{cn}...[/blue]")
                    # Get plugin instance
                    if not self.plugin_manager:
                        console.print(
                            "[red]Error:[/red] Plugin manager not initialized"
                        )
                        return

                    plugin = self.plugin_manager.get_plugin(pn)
                    if plugin and hasattr(plugin, ci.get("handler", "")):
                        handler = getattr(plugin, ci.get("handler", ""))
                        if callable(handler):
                            handler()
                        else:
                            console.print(
                                f"[red]Error:[/red] Handler not callable: {ci.get('handler')}"
                            )
                    else:
                        console.print(
                            f"[yellow]Plugin {pn} command {cn} is not yet implemented[/yellow]"
                        )
                        console.print(
                            f"[dim]Description: {ci.get('description', 'No description')}[/dim]"
                        )

                # Register command to app
                app.command(name=command_name)(command_wrapper)


# Global state instance
state = AppState()


@app.callback()
def main(
    config_dir: Path = typer.Option(
        Path("config"),
        "--config-dir",
        "-c",
        help="Configuration directory path",
    ),
) -> None:
    """
    Learning Assistant - A modular AI learning assistant CLI tool.

    Initialize core components before executing commands.
    """
    # Initialize global state
    state.initialize(config_dir)


@app.command()
def version() -> None:
    """Show the version of Learning Assistant."""
    console.print(f"[bold green]Learning Assistant[/bold green] version: {__version__}")

    # Show loaded plugins count
    if state.plugin_manager:
        plugins = state.plugin_manager.get_all_plugins()
        console.print(f"[blue]Loaded plugins:[/blue] {len(plugins)}")


@app.command()
def setup() -> None:
    """Interactive setup wizard for first-time configuration."""
    console.print("[bold blue]Welcome to Learning Assistant Setup Wizard![/bold blue]")

    # Check Python version
    import sys

    console.print(f"\n[yellow]Python Version:[/yellow] {sys.version}")

    # Generate default configuration files
    console.print("\n[yellow]Generating default configuration...[/yellow]")

    if state.config_manager:
        state.config_manager.generate_default_config()
        console.print("[green][OK][/green] Default configuration files generated")

        # Load configuration to verify
        state.config_manager.load_all()
        console.print("[green][OK][/green] Configuration loaded successfully")

    # Check FFmpeg
    try:
        import subprocess

        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[green][OK][/green] FFmpeg is installed")
        else:
            console.print("[red][X][/red] FFmpeg is not installed")
    except FileNotFoundError:
        console.print(
            "[red][X][/red] FFmpeg is not installed (required for video processing)"
        )

    # Check and validate API keys

    console.print("\n[yellow]Validating API Keys:[/yellow]")

    if state.config_manager:
        llm_config = state.config_manager.get_llm_config()

        if llm_config:
            provider = llm_config.get("provider")
            api_key = llm_config.get("api_key")

            if api_key and provider:
                console.print(f"[blue]Testing {provider} API key...[/blue]")

                # Validate API key by making a test request
                try:
                    from learning_assistant.core.llm.service import LLMService

                    model = llm_config.get("model", "gpt-4o")
                    llm_service = LLMService(
                        provider=provider,
                        api_key=api_key,
                        model=model,
                    )

                    if llm_service.validate_api_key():
                        console.print(
                            f"[green][OK][/green] {provider} API key is valid"
                        )
                    else:
                        console.print(f"[red][X][/red] {provider} API key is invalid")
                except Exception as e:
                    console.print(
                        f"[red][X][/red] {provider} API key validation failed: {e}"
                    )
            else:
                console.print("[red][X][/red] API key or provider is not set")

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("[yellow]Next steps:[/yellow]")
    console.print("  1. Install FFmpeg if needed: https://ffmpeg.org/download.html")
    console.print("  2. Set API keys in environment variables or config/settings.local.yaml")
    console.print("  3. Prefer editing config/settings.local.yaml for local customization")
    console.print("  4. Run: la list-plugins to see available modules")
    console.print("  5. Run: la video <video_url> to process a video")


@app.command("list-plugins")
def list_plugins_cmd() -> None:
    """List all discovered and loaded plugins."""
    if not state.plugin_manager:
        console.print("[red]Error:[/red] Plugin manager not initialized")
        return

    console.print("[bold blue]Plugin Information:[/bold blue]")

    # Get all discovered plugins
    discovered_plugins = state.plugin_manager.plugins

    # Create table for discovered plugins
    table = Table(title="Discovered Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Version", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Priority", style="magenta")

    for plugin_metadata in discovered_plugins.values():
        status = (
            "[green]Loaded[/green]"
            if plugin_metadata.name in state.plugin_manager.loaded_plugins
            else "[red]Not Loaded[/red]"
        )
        priority = str(plugin_metadata.priority) if plugin_metadata.priority else "-"
        table.add_row(
            plugin_metadata.name,
            plugin_metadata.type,
            plugin_metadata.version,
            status,
            priority,
        )

    console.print(table)

    # Show loaded plugins count
    loaded_count = len(state.plugin_manager.loaded_plugins)
    console.print(
        f"\n[blue]Total loaded:[/blue] {loaded_count}/{len(discovered_plugins)}"
    )


@app.command()
def config() -> None:
    """Show current configuration."""
    if not state.config_manager:
        console.print("[red]Error:[/red] Config manager not initialized")
        return

    console.print("[bold blue]Current Configuration:[/bold blue]")

    # Show LLM configuration
    try:
        llm_config = state.config_manager.get_llm_config()
        console.print("\n[yellow]LLM Configuration:[/yellow]")
        console.print(f"  Provider: {llm_config.get('provider')}")
        console.print(f"  Model: {llm_config.get('model')}")
        console.print(
            f"  API Key: {'[OK] Set' if llm_config.get('api_key') else '[X] Not Set'}"
        )
        console.print(f"  Temperature: {llm_config.get('temperature')}")
        console.print(f"  Max Tokens: {llm_config.get('max_tokens')}")
    except ValueError as e:
        console.print(f"[red]Error loading LLM config:[/red] {e}")

    # Show cost tracking
    if state.config_manager.settings_model:
        cost_tracking = state.config_manager.settings_model.llm.cost_tracking
        console.print("\n[yellow]Cost Tracking:[/yellow]")
        console.print(f"  Enabled: {cost_tracking.enabled}")
        console.print(f"  Daily Limit: ${cost_tracking.daily_limit}")
        console.print(f"  Warn Threshold: ${cost_tracking.warning_threshold}")

    console.print("\n[yellow]Config Files:[/yellow]")
    console.print("  Primary local override: config/settings.local.yaml")
    console.print("  Default settings: config/settings.yaml")
    console.print("  Default module template: config/modules.yaml")
    console.print("  Default adapter template: config/adapters.yaml")


@app.command()
def history() -> None:
    """Show learning history."""
    console.print("[bold blue]Learning History:[/bold blue]")
    console.print("[yellow]No history records found[/yellow]")
    console.print(
        "[dim]History tracking will be enabled after processing first video[/dim]"
    )


@app.command()
def link(
    url: str = typer.Argument(..., help="Web URL to process"),
    provider: str = typer.Option(
        None, "--provider", "-p", help="LLM provider (openai, anthropic, deepseek)"
    ),
    model: str = typer.Option(None, "--model", "-m", help="LLM model to use"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format (markdown, json)"
    ),
    no_quiz: bool = typer.Option(False, "--no-quiz", help="Skip quiz generation"),
) -> None:
    """
    Extract knowledge from web link and generate knowledge card.

    Example: la link https://example.com/article
    """
    import asyncio
    from datetime import datetime

    from learning_assistant.modules.link_learning import LinkLearningModule

    console.print(f"[bold blue]Processing web link:[/bold blue] {url}")

    try:
        # Initialize LinkLearningModule
        with console.status("[bold green]Initializing...") as status:
            module = LinkLearningModule()

            # Get configuration from state
            if not state.config_manager or not state.event_bus:
                console.print(
                    "[red]Error:[/red] Configuration not initialized. Run 'la setup' first."
                )
                return

            # Build config
            config_full = state.config_manager.modules_model.model_dump().get(
                "link_learning", {}
            )
            # Extract 'config' sub-key if present
            config = config_full.get("config", config_full)

            # Override with CLI options
            if provider:
                config.setdefault("llm", {})["provider"] = provider
            if model:
                config.setdefault("llm", {})["model"] = model
            if no_quiz:
                config.setdefault("features", {})["generate_quiz"] = False

            # Initialize module
            module.initialize(config, state.event_bus)

        # Process URL
        with console.status("[bold green]Fetching and analyzing content...") as status:
            # Run async process
            knowledge_card = asyncio.run(module.process(url))

        # Display results
        console.print(
            "\n[bold green][OK] Knowledge card generated successfully![/bold green]\n"
        )

        # Create table for display
        table = Table(
            title="Knowledge Card", show_header=True, header_style="bold blue"
        )
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row("Title", knowledge_card.title)
        table.add_row("Source", knowledge_card.source)
        table.add_row("URL", knowledge_card.url)
        table.add_row("Word Count", str(knowledge_card.word_count))
        table.add_row("Reading Time", knowledge_card.reading_time)
        table.add_row("Difficulty", knowledge_card.difficulty)
        table.add_row("Tags", ", ".join(knowledge_card.tags))

        console.print(table)

        # Display summary
        console.print("\n[bold cyan]Summary:[/bold cyan]")
        console.print(f"{knowledge_card.summary}\n")

        # Display key points
        console.print("[bold cyan]Key Points:[/bold cyan]")
        for i, point in enumerate(knowledge_card.key_points, 1):
            console.print(f"  {i}. {point}")

        # Display key concepts
        if knowledge_card.key_concepts:
            console.print("\n[bold cyan]Key Concepts:[/bold cyan]")
            for i, concept in enumerate(knowledge_card.key_concepts, 1):
                console.print(f"\n  [bold]{i}. {concept.term}[/bold]")
                console.print(f"  {concept.definition}")

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format == "json":
                import json

                with output_path.open("w", encoding="utf-8") as f:
                    json.dump(knowledge_card.to_dict(), f, ensure_ascii=False, indent=2)
            else:  # markdown
                # Generate markdown content using new structure
                md_content = f"""# {knowledge_card.title}

**Source**: {knowledge_card.source}
**URL**: {knowledge_card.url}
**Word Count**: {knowledge_card.word_count}
**Reading Time**: {knowledge_card.reading_time}
**Difficulty**: {knowledge_card.difficulty}
**Created**: {knowledge_card.created_at.strftime('%Y-%m-%d %H:%M:%S')}

## Summary

{knowledge_card.summary}

## Key Points

"""
                for i, point in enumerate(knowledge_card.key_points, 1):
                    md_content += f"{i}. {point}\n"

                if knowledge_card.key_concepts:
                    md_content += "\n## Key Concepts\n\n"
                    for concept in knowledge_card.key_concepts:
                        md_content += f"### {concept.term}\n\n{concept.definition}\n\n"

                if knowledge_card.tags:
                    md_content += f"\n## Tags\n\n{', '.join(knowledge_card.tags)}\n"

                with output_path.open("w", encoding="utf-8") as f:
                    f.write(md_content)

            console.print(f"\n[green][OK] Saved to: {output_path}[/green]")

        console.print(
            f"\n[dim]Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error processing URL:[/red] {e}")
        raise typer.Exit(code=1)


# Vocabulary Learning Command
@app.command()
def vocabulary(
    text: str = typer.Option(
        "", "--text", "-t", help="Source text to extract words from"
    ),
    file: Path = typer.Option(None, "--file", "-f", help="Input file path"),
    url: str = typer.Option(None, "--url", "-u", help="Web URL to extract content from"),
    word_count: int = typer.Option(
        10, "--count", "-c", help="Number of words to extract (1-50)"
    ),
    difficulty: str = typer.Option(
        "intermediate",
        "--difficulty",
        "-d",
        help="Difficulty level (beginner/intermediate/advanced)",
    ),
    no_story: bool = typer.Option(False, "--no-story", help="Skip story generation"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """
    Extract vocabulary and generate word cards.

    Examples:
        la vocabulary --text "Your text here..."
        la vocabulary --file article.txt --count 15
        la vocabulary --url https://example.com/article --count 10
        la vocabulary --text "..." --difficulty advanced --no-story
    """
    import asyncio
    from datetime import datetime

    from learning_assistant.modules.vocabulary import VocabularyLearningModule

    # Get content
    content = text
    source_type = "text"

    if url:
        # Fetch content from URL
        console.print(f"[bold blue]Fetching content from URL:[/bold blue] {url}")
        try:
            from learning_assistant.modules.link_learning.content_fetcher import ContentFetcher
            from learning_assistant.modules.link_learning.content_parser import ContentParser
            import asyncio as aio

            fetcher = ContentFetcher(timeout=30, max_retries=3)
            # Use lower min_content_length for vocabulary extraction
            parser = ContentParser(engine="trafilatura", min_content_length=10)

            html = aio.run(fetcher.fetch(url))
            if not html:
                console.print(f"[red]Error:[/red] Failed to fetch URL: {url}")
                raise typer.Exit(code=1)

            parsed = parser.parse(html, url)
            content = parsed.content  # Access content attribute
            source_type = "url"

            if not content.strip():
                console.print(f"[red]Error:[/red] No content extracted from URL")
                raise typer.Exit(code=1)

            console.print(f"[green]OK[/green] Fetched {len(content)} characters")
        except Exception as e:
            console.print(f"[red]Error fetching URL:[/red] {e}")
            raise typer.Exit(code=1)
    elif file:
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(code=1)
        with file.open("r", encoding="utf-8") as f:
            content = f.read()
        source_type = "file"

    if not content.strip():
        console.print("[red]Error:[/red] No content provided. Use --text, --file, or --url")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Extracting vocabulary:[/bold blue] {word_count} words")

    try:
        # Initialize VocabularyLearningModule
        with console.status("[bold green]Initializing...") as status:
            module = VocabularyLearningModule()

            # Get configuration from state
            if not state.config_manager or not state.event_bus:
                console.print(
                    "[red]Error:[/red] Configuration not initialized. Run 'la setup' first."
                )
                return

            # Build config
            config_full = state.config_manager.modules_model.model_dump().get(
                "vocabulary", {}
            )
            config = config_full.get("config", config_full)

            # Merge global LLM config
            if state.config_manager:
                global_llm_config = state.config_manager.get_llm_config()
                if global_llm_config and "api_key" in global_llm_config:
                    if "llm" not in config:
                        config["llm"] = {}
                    if "api_key" not in config["llm"]:
                        config["llm"]["api_key"] = global_llm_config["api_key"]
                    if (
                        "base_url" not in config["llm"]
                        and "base_url" in global_llm_config
                    ):
                        config["llm"]["base_url"] = global_llm_config["base_url"]

            # Initialize module
            module.initialize(config, state.event_bus)

        # Process content
        with console.status(
            "[bold green]Extracting words and generating cards..."
        ) as status:
            result = asyncio.run(
                module.process(
                    content=content,
                    word_count=word_count,
                    difficulty=difficulty,
                    generate_story=not no_story,
                )
            )

        # Display results
        console.print(
            f"\n[bold green][OK] Extracted {len(result.vocabulary_cards)} words![/bold green]\n"
        )

        # Create table for words
        table = Table(
            title="Vocabulary Cards", show_header=True, header_style="bold blue"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Word", style="cyan", width=20)
        table.add_column("Phonetic", style="yellow", width=25)
        table.add_column("Difficulty", style="green", width=12)

        for i, card in enumerate(result.vocabulary_cards, 1):
            # Handle Windows encoding issue with IPA phonetic symbols
            phonetic_str = card.phonetic.us or card.phonetic.uk or "-"
            # On Windows, skip displaying IPA symbols if they cause encoding issues
            try:
                # Test if phonetic can be encoded in console encoding
                phonetic_str.encode(sys.stdout.encoding or 'utf-8')
            except (UnicodeEncodeError, AttributeError):
                # Fall back to placeholder on Windows with GBK encoding
                phonetic_str = "[See file]"

            table.add_row(
                str(i),
                card.word,
                phonetic_str,
                card.difficulty,
            )

        console.print(table)

        # Display story if generated
        if result.context_story:
            console.print("\n[bold cyan]Context Story:[/bold cyan]")
            console.print(f"[bold]{result.context_story.title}[/bold]")
            console.print(f"{result.context_story.content[:200]}...")
            console.print(f"[dim]Word count: {result.context_story.word_count}[/dim]")

        # Display statistics
        if result.statistics:
            console.print("\n[bold cyan]Statistics:[/bold cyan]")
            dist = result.statistics.get("difficulty_distribution", {})
            console.print(f"  Beginner: {dist.get('beginner', 0)}")
            console.print(f"  Intermediate: {dist.get('intermediate', 0)}")
            console.print(f"  Advanced: {dist.get('advanced', 0)}")

        # Save output
        if output:
            output_path = Path(output)
        else:
            output_dir = Path(
                config.get("output", {}).get("directory", "data/outputs/vocabulary")
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"vocabulary_{timestamp}.md"

        # Export to Markdown
        with console.status("[bold green]Saving output..."):
            md_content = _generate_vocabulary_markdown(result)
            with output_path.open("w", encoding="utf-8") as f:
                f.write(md_content)

        console.print(f"\n[green][OK] Saved to: {output_path}[/green]")
        console.print(
            f"[dim]Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error extracting vocabulary:[/red] {e}")
        raise typer.Exit(code=1)


def _generate_vocabulary_markdown(result) -> str:
    """Generate Markdown output for vocabulary."""
    from datetime import datetime

    md_content = f"""# Vocabulary Learning Cards

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics

- **Total Words**: {result.statistics.get('total_words', 0)}
- **Difficulty Distribution**:
  - Beginner: {result.statistics.get('difficulty_distribution', {}).get('beginner', 0)}
  - Intermediate: {result.statistics.get('difficulty_distribution', {}).get('intermediate', 0)}
  - Advanced: {result.statistics.get('difficulty_distribution', {}).get('advanced', 0)}

---

## Vocabulary Cards

"""

    for card in result.vocabulary_cards:
        md_content += f"### {card.word}\n\n"

        # Phonetic
        if card.phonetic.us or card.phonetic.uk:
            md_content += "**Phonetic**: "
            if card.phonetic.us:
                md_content += f"US {card.phonetic.us} "
            if card.phonetic.uk:
                md_content += f"UK {card.phonetic.uk}"
            md_content += "\n\n"

        # Part of speech and definition
        md_content += f"**{card.part_of_speech}**\n\n"
        md_content += f"- **Chinese**: {card.definition.zh}\n"
        if card.definition.en:
            md_content += f"- **English**: {card.definition.en}\n"
        md_content += "\n"

        # Examples
        md_content += "**Example Sentences**:\n\n"
        for i, ex in enumerate(card.example_sentences, 1):
            md_content += f"{i}. {ex.sentence}\n"
            md_content += f"   *{ex.translation}* [{ex.context}]\n\n"

        # Synonyms and antonyms
        if card.synonyms:
            md_content += f"**Synonyms**: {', '.join(card.synonyms)}\n\n"
        if card.antonyms:
            md_content += f"**Antonyms**: {', '.join(card.antonyms)}\n\n"

        # Related words
        if card.related_words:
            md_content += f"**Related Words**: {', '.join(card.related_words)}\n\n"

        # Metadata
        md_content += (
            f"**Difficulty**: {card.difficulty} | **Frequency**: {card.frequency}\n\n"
        )
        md_content += "---\n\n"

    # Context story
    if result.context_story:
        md_content += f"""## Context Story

### {result.context_story.title}

{result.context_story.content}

**Word Count**: {result.context_story.word_count} | **Difficulty**: {result.context_story.difficulty}

**Target Words**: {', '.join(result.context_story.target_words)}
"""

    return md_content


# Video Summary Command
@app.command()
def video(
    url: str = typer.Argument(..., help="Video URL to process"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format (markdown, json, pdf)"
    ),
) -> None:
    """
    Summarize video content (MVP module).

    Example: la video https://www.bilibili.com/video/BV123
    """
    from datetime import datetime

    from learning_assistant.modules.video_summary import VideoSummaryModule

    console.print(f"[bold blue]Processing video:[/bold blue] {url}")

    try:
        # Initialize VideoSummaryModule
        with console.status("[bold green]Initializing...") as status:
            module = VideoSummaryModule()

            # Get configuration from state
            if not state.config_manager or not state.event_bus:
                console.print(
                    "[red]Error:[/red] Configuration not initialized. Run 'la setup' first."
                )
                return

            # Build config
            video_summary_data = state.config_manager.modules_model.model_dump().get(
                "video_summary", {}
            )
            config = video_summary_data.get("config", video_summary_data)

            # Merge global LLM config with module-specific config
            if state.config_manager:
                global_llm_config = state.config_manager.get_llm_config()
                if global_llm_config and "api_key" in global_llm_config:
                    # Module-specific LLM config takes precedence, but use global api_key
                    if "llm" not in config:
                        config["llm"] = {}
                    # Set API key from global config if not in module config
                    if "api_key" not in config["llm"]:
                        config["llm"]["api_key"] = global_llm_config["api_key"]
                    # Also copy base_url if not set
                    if (
                        "base_url" not in config["llm"]
                        and "base_url" in global_llm_config
                    ):
                        config["llm"]["base_url"] = global_llm_config["base_url"]

            # Initialize module
            module.initialize(config, state.event_bus)

        console.print("\n[yellow]Video processing steps:[/yellow]")
        console.print("  1. Downloading video... (this may take a few minutes)")
        console.print("  2. Extracting audio...")
        console.print("  3. Transcribing audio...")
        console.print("  4. Generating summary...")
        console.print(
            "\n[dim]Please wait, this process may take 5-10 minutes for longer videos...[/dim]\n"
        )

        # Process video
        with console.status("[bold green]Processing video...") as status:
            # Run execute (synchronous method)
            result = module.execute({"url": url})

        # Display results
        console.print(
            "\n[bold green][OK] Video summary generated successfully![/bold green]\n"
        )

        # Create table for display
        table = Table(title="Video Summary", show_header=True, header_style="bold blue")
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row("Title", result.get("metadata", {}).get("title", "Unknown"))
        table.add_row("Platform", result.get("metadata", {}).get("platform", "Unknown"))
        table.add_row(
            "Duration", f"{result.get('metadata', {}).get('duration', 0)} seconds"
        )

        console.print(table)

        # Display summary
        summary_data = result.get("summary", {})
        if summary_data.get("content"):
            console.print("\n[bold cyan]Summary:[/bold cyan]")
            console.print(f"{summary_data['content']}\n")

        # Display key points
        if summary_data.get("key_points"):
            console.print("[bold cyan]Key Points:[/bold cyan]")
            for i, point in enumerate(summary_data["key_points"], 1):
                console.print(f"  {i}. {point}")

        # Display knowledge points
        if summary_data.get("knowledge"):
            console.print("\n[bold cyan]Knowledge Points:[/bold cyan]")
            for i, point in enumerate(summary_data["knowledge"], 1):
                console.print(f"  {i}. {point}")

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format == "json":
                import json

                with output_path.open("w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            else:  # markdown
                # Generate markdown content
                md_content = f"""# {result.get('metadata', {}).get('title', 'Video Summary')}

**Platform**: {result.get('metadata', {}).get('platform', 'Unknown')}
**URL**: {url}
**Duration**: {result.get('metadata', {}).get('duration', 0)} seconds
**Processed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

{summary_data.get('content', 'No summary available')}

## Key Points

"""
                for i, point in enumerate(summary_data.get("key_points", []), 1):
                    md_content += f"{i}. {point}\n"

                if summary_data.get("knowledge"):
                    md_content += "\n## Knowledge Points\n\n"
                    for i, point in enumerate(summary_data["knowledge"], 1):
                        md_content += f"{i}. {point}\n"

                # Add transcript if available
                transcript = result.get("transcript", "")
                if transcript:
                    md_content += f"\n## Transcript\n\n{transcript}\n"

                with output_path.open("w", encoding="utf-8") as f:
                    f.write(md_content)

            console.print(f"\n[green][OK] Saved to: {output_path}[/green]")

        # Display output files
        files = result.get("files", {})
        if files:
            console.print("\n[bold cyan]Output Files:[/bold cyan]")
            if files.get("summary_path"):
                console.print(f"  Summary: {files['summary_path']}")
            if files.get("subtitle_path"):
                console.print(f"  Subtitles: {files['subtitle_path']}")

        console.print(
            f"\n[dim]Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error processing video:[/red] {e}")
        console.print(f"[dim]Error type: {type(e).__name__}[/dim]")
        raise typer.Exit(code=1)


# Auth commands
@auth_app.command("login")
def auth_login(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform: bilibili"),
    timeout: int = typer.Option(
        180, "--timeout", "-t", help="QR code timeout (seconds)"
    ),
) -> None:
    """
    Authenticate with platform using QR code.

    Example: la auth login --platform bilibili
    """
    if not state.auth_manager:
        console.print("[red]Error:[/red] Auth manager not initialized")
        raise typer.Exit(code=1)

    try:
        # Check if platform is supported
        supported = state.auth_manager.get_supported_platforms()
        if platform not in supported:
            console.print(f"[red]Error:[/red] Platform '{platform}' not supported")
            console.print(
                f"[yellow]Supported platforms:[/yellow] {', '.join(supported)}"
            )
            raise typer.Exit(code=1)

        console.print(f"[bold blue]Authenticating with {platform}...[/bold blue]\n")

        # Execute login
        result = state.auth_manager.login(platform, timeout=timeout)

        if result.success:
            console.print("\n[bold green][OK] Authentication successful![/bold green]")
            if result.user_id:
                console.print(f"[blue]User ID:[/blue] {result.user_id}")
            if result.cookie_file:
                console.print(f"[blue]Cookie file:[/blue] {result.cookie_file}")
            console.print(
                "\n[green]You can now download videos with authenticated access.[/green]"
            )
        else:
            console.print(
                f"\n[red][X] Authentication failed:[/red] {result.error_message}"
            )
            raise typer.Exit(code=1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error during authentication:[/red] {e}")
        raise typer.Exit(code=1)


@auth_app.command("status")
def auth_status(
    platform: str = typer.Option(
        "all", "--platform", "-p", help="Platform to check (or 'all')"
    ),
) -> None:
    """
    Check authentication status for platform(s).

    Example: la auth status --platform bilibili
    """
    if not state.auth_manager:
        console.print("[red]Error:[/red] Auth manager not initialized")
        raise typer.Exit(code=1)

    try:
        platforms_to_check = (
            state.auth_manager.get_supported_platforms()
            if platform == "all"
            else [platform]
        )

        print("\nAuthentication Status:")
        print("=" * 70)

        for plat in platforms_to_check:
            info = state.auth_manager.check_status(plat)

            status_str = (
                "[OK] Authenticated"
                if info.status.value == "authenticated"
                else (
                    "[X] Not Authenticated"
                    if info.status.value == "not_authenticated"
                    else "[?] Invalid"
                )
            )

            print(f"\nPlatform: {plat}")
            print(f"  Status: {status_str}")
            if info.user_id:
                print(f"  User ID: {info.user_id}")
            if info.cookie_file:
                print(f"  Cookie File: {info.cookie_file}")

        print("\n" + "=" * 70)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error checking status:[/red] {e}")
        raise typer.Exit(code=1)


@auth_app.command("logout")
def auth_logout(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform to logout"),
) -> None:
    """
    Clear authentication for platform.

    Example: la auth logout --platform bilibili
    """
    if not state.auth_manager:
        console.print("[red]Error:[/red] Auth manager not initialized")
        raise typer.Exit(code=1)

    try:
        success = state.auth_manager.logout(platform)

        if success:
            console.print(f"[green][OK] Logged out from {platform}[/green]")
        else:
            console.print(f"[yellow]No active session for {platform}[/yellow]")

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error during logout:[/red] {e}")
        raise typer.Exit(code=1)


@auth_app.command("import")
def auth_import(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform: douyin"),
    cookies: str = typer.Option(
        ..., "--cookies", "-c", help="Cookie string from browser"
    ),
) -> None:
    """
    Import cookies manually for platforms that don't support QR login.

    Example: la auth import --platform douyin --cookies "odin_tt=xxx; ttwid=yyy"

    Note: Get cookies from browser DevTools (F12 -> Network -> Copy cookie header)
    """
    if not state.auth_manager:
        console.print("[red]Error:[/red] Auth manager not initialized")
        raise typer.Exit(code=1)

    try:
        # Check if platform is supported
        supported = state.auth_manager.get_supported_platforms()
        if platform not in supported:
            console.print(f"[red]Error:[/red] Platform '{platform}' not supported")
            console.print(
                f"[yellow]Supported platforms:[/yellow] {', '.join(supported)}"
            )
            raise typer.Exit(code=1)

        # Get provider
        provider = state.auth_manager.providers.get(platform)
        if not provider:
            console.print(f"[red]Error:[/red] Provider not found for {platform}")
            raise typer.Exit(code=1)

        # Check if provider supports import
        if not hasattr(provider, "import_cookies"):
            console.print(
                f"[red]Error:[/red] Platform '{platform}' does not support manual cookie import"
            )
            console.print(
                f"[yellow]Use 'la auth login --platform {platform}' instead[/yellow]"
            )
            raise typer.Exit(code=1)

        console.print(f"[bold blue]Importing cookies for {platform}...[/bold blue]\n")

        # Import cookies
        result = provider.import_cookies(cookies)

        if result.success:
            console.print(
                "[bold green][OK] Cookies imported successfully![/bold green]"
            )
            if result.cookie_file:
                console.print(f"[blue]Cookie file:[/blue] {result.cookie_file}")
            console.print(
                "\n[green]You can now download videos with authenticated access.[/green]"
            )
        else:
            console.print(f"\n[red][X] Import failed:[/red] {result.error_message}")
            raise typer.Exit(code=1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error importing cookies:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
