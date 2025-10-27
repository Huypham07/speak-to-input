from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional

from domain.plugins.base_intent_plugin import IntentPlugin
from shared.logging import get_logger

logger = get_logger(__name__)


class IntentPluginRegistry:
    """
    Registry for intent plugins.
    Auto-discovers plugins from the plugins directory.
    """

    def __init__(self):
        self._plugins: Dict[str, IntentPlugin] = {}

    def discover_plugins(self) -> None:
        """
        Auto-discover all intent plugins.
        Scans the plugins directory and loads all *_plugin.py files.
        """
        # Get plugins directory
        plugins_dir = Path(__file__).parent

        logger.info(f'Discovering intent plugins in {plugins_dir}')

        # Scan for plugin files
        for file_path in plugins_dir.glob('*_plugin.py'):
            if file_path.name == 'base_intent_plugin.py':
                continue

            try:
                # Import module
                module_name = f'domain.plugins.{file_path.stem}'
                module = importlib.import_module(module_name)

                # Find plugin classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, IntentPlugin) and
                        obj != IntentPlugin and
                        not inspect.isabstract(obj)
                    ):

                        # Instantiate plugin
                        plugin = obj()

                        # Register
                        self._plugins[plugin.intent_type] = plugin
                        logger.info(f'Registered plugin: {plugin.intent_type} ({plugin.display_name})')

            except Exception as e:
                logger.error(f'Failed to load plugin {file_path.name}: {e}')

    def get_plugin(self, intent_type: str) -> Optional[IntentPlugin]:
        """Get plugin by intent type"""
        return self._plugins.get(intent_type)

    def list_plugins(self) -> List[IntentPlugin]:
        """List all registered plugins"""
        return list(self._plugins.values())

    def has_plugin(self, intent_type: str) -> bool:
        """Check if plugin exists"""
        return intent_type in self._plugins


# Global registry instance
_registry = IntentPluginRegistry()


def get_plugin_registry() -> IntentPluginRegistry:
    """Get the global plugin registry"""
    return _registry


def get_intent_plugin(intent_type: str) -> Optional[IntentPlugin]:
    """Get plugin for intent type"""
    return _registry.get_plugin(intent_type)


def initialize_plugins() -> None:
    """Initialize and discover all plugins"""
    _registry.discover_plugins()
