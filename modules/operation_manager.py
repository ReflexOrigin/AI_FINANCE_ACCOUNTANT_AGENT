"""
Operation Manager Module for Finance Accountant Agent

This module serves as the central router for operations within the Finance Agent.
It dynamically registers available operations from the operations directory
and routes user intents to the appropriate operation handler.

Features:
- Dynamic operation registration
- Intent-to-operation routing
- Operation execution with error handling
- Fallback mechanisms for unrecognized intents
- Metrics tracking for operations

Dependencies:
- importlib: For dynamic operation module loading
- Operation modules from operations/ directory
"""

import asyncio
import importlib
import inspect
import logging
import time
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from typing import List, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)


class OperationRegistry:
    """Registry of all available operations and their handlers."""

    def __init__(self):
        self.operations: Dict[(str, str), Callable] = {}  # intent/subintent → handler
        self.modules: Dict[str, Any] = {}

    def register(self, intent: str, subintent: str, handler: Callable):
        """Register a handler for a given intent/subintent."""
        key = (intent, subintent)
        self.operations[key] = handler
        logger.debug(f"Registered handler for {intent}/{subintent}")

    def get_handler(self, intent: str, subintent: str) -> Optional[Callable]:
        """Retrieve the handler for the specified intent/subintent."""
        return self.operations.get((intent, subintent))

    def register_module(self, module_name: str, module):
        """Keep track of a loaded operations module."""
        self.modules[module_name] = module

    def list_operations(self) -> List[Tuple[str, str]]:
        """List all registered intent/subintent pairs."""
        return list(self.operations.keys())


class OperationManager:
    """
    Manages the registration, discovery, and execution of finance operations.
    """

    def __init__(self):
        self.registry = OperationRegistry()
        self.load_operations()

    def load_operations(self):
        """Dynamically load all operation modules and register their handlers."""
        base_dir = Path(__file__).parent / "operations"

        try:
            for file_path in base_dir.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue

                module_name = file_path.stem
                module_path = f"modules.operations.{module_name}"

                try:
                    module = import_module(module_path)
                    self.registry.register_module(module_name, module)

                    for name, obj in inspect.getmembers(module):
                        if name.startswith("handle_") and inspect.iscoroutinefunction(obj):
                            subintent = name[len("handle_"):]
                            self.registry.register(module_name, subintent, obj)
                    logger.info(f"Loaded operation module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load module {module_name}: {e}")

        except Exception as e:
            logger.error(f"Error loading operations directory: {e}")

    async def execute_operation(self, intent_data: Dict) -> Dict:
        """
        Execute the appropriate operation based on intent_data.

        Args:
            intent_data: {'intent': str, 'subintent': str, 'entities': dict, ...}

        Returns:
            dict: operation result (with metadata/error info)
        """
        intent = intent_data.get("intent", "unknown")
        subintent = intent_data.get("subintent", "unknown")
        entities = intent_data.get("entities", {})

        handler = self.registry.get_handler(intent, subintent)
        if handler:
            logger.info(f"Executing {intent}/{subintent}")
            start = time.time()
            try:
                result = await handler(entities)
                elapsed = time.time() - start

                if isinstance(result, dict):
                    result.setdefault("_metadata", {})
                    result["_metadata"].update({
                        "operation": f"{intent}/{subintent}",
                        "execution_time": elapsed,
                        "success": True,
                    })
                else:
                    result = {
                        "result": result,
                        "_metadata": {
                            "operation": f"{intent}/{subintent}",
                            "execution_time": elapsed,
                            "success": True,
                        }
                    }
                return result

            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"Error in {intent}/{subintent}: {e}")
                return {
                    "error": str(e),
                    "_metadata": {
                        "operation": f"{intent}/{subintent}",
                        "execution_time": elapsed,
                        "success": False,
                    }
                }

        else:
            logger.warning(f"No handler for {intent}/{subintent}")
            return {
                "error": f"No handler for {intent}/{subintent}",
                "_metadata": {"operation": "unknown", "success": False}
            }

    def list_available_operations(self) -> List[Dict]:
        """
        List all registered operations in a structured list.

        Returns:
            List of {'intent': str, 'subintent': str, 'handler': str}
        """
        ops = []
        for intent, subintent in self.registry.list_operations():
            handler = self.registry.get_handler(intent, subintent)
            ops.append({
                "intent": intent,
                "subintent": subintent,
                "handler": handler.__name__ if handler else None
            })
        return ops
