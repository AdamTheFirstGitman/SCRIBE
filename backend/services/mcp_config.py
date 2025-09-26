#!/usr/bin/env python3
"""
Configuration MCP pour surveillance Render
Setup et validation des endpoints MCP
"""

import os
import json
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from backend.utils.logger import get_logger

logger = get_logger("mcp_config")

@dataclass
class MCPEndpoint:
    """Configuration d'un endpoint MCP"""
    name: str
    url: str
    auth_type: str  # bearer, api_key, etc.
    credentials: Dict[str, str]
    timeout: int = 30
    retry_count: int = 3

class MCPConfigManager:
    """Gestionnaire de configuration MCP"""

    def __init__(self):
        self.endpoints: Dict[str, MCPEndpoint] = {}
        self.validated_endpoints: Dict[str, bool] = {}

    def add_render_endpoint(self, api_key: str):
        """Ajouter l'endpoint Render MCP"""
        render_endpoint = MCPEndpoint(
            name="render",
            url="https://mcp.render.com/mcp",
            auth_type="bearer",
            credentials={"token": api_key},
            timeout=30,
            retry_count=3
        )
        self.endpoints["render"] = render_endpoint

    def add_custom_endpoint(self, name: str, url: str, credentials: Dict[str, str]):
        """Ajouter un endpoint MCP personnalisé"""
        endpoint = MCPEndpoint(
            name=name,
            url=url,
            auth_type="bearer",
            credentials=credentials
        )
        self.endpoints[name] = endpoint

    async def validate_endpoint(self, endpoint_name: str) -> bool:
        """Valider la connectivité d'un endpoint MCP"""
        if endpoint_name not in self.endpoints:
            logger.error(f"Endpoint '{endpoint_name}' not configured")
            return False

        endpoint = self.endpoints[endpoint_name]

        try:
            headers = self._build_headers(endpoint)
            timeout = aiohttp.ClientTimeout(total=endpoint.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test de connectivité basique
                async with session.get(
                    f"{endpoint.url}/health",  # Endpoint de santé supposé
                    headers=headers
                ) as response:
                    success = response.status in [200, 404]  # 404 OK si endpoint health n'existe pas

                    if success:
                        self.validated_endpoints[endpoint_name] = True
                        logger.info(
                            f"MCP endpoint validated",
                            endpoint=endpoint_name,
                            url=endpoint.url,
                            status_code=response.status
                        )
                    else:
                        logger.error(
                            f"MCP endpoint validation failed",
                            endpoint=endpoint_name,
                            url=endpoint.url,
                            status_code=response.status
                        )

                    return success

        except Exception as e:
            logger.error(
                f"MCP endpoint validation error",
                endpoint=endpoint_name,
                error=str(e)
            )
            return False

    async def validate_all_endpoints(self) -> Dict[str, bool]:
        """Valider tous les endpoints configurés"""
        results = {}
        for endpoint_name in self.endpoints:
            results[endpoint_name] = await self.validate_endpoint(endpoint_name)
        return results

    def _build_headers(self, endpoint: MCPEndpoint) -> Dict[str, str]:
        """Construire les headers pour l'authentification"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SCRIBE-MCP/1.0"
        }

        if endpoint.auth_type == "bearer":
            token = endpoint.credentials.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif endpoint.auth_type == "api_key":
            api_key = endpoint.credentials.get("api_key")
            key_header = endpoint.credentials.get("key_header", "X-API-Key")
            if api_key:
                headers[key_header] = api_key

        return headers

    def get_session_config(self, endpoint_name: str) -> Optional[Dict[str, Any]]:
        """Obtenir la configuration de session pour un endpoint"""
        if endpoint_name not in self.endpoints:
            return None

        endpoint = self.endpoints[endpoint_name]
        return {
            "base_url": endpoint.url,
            "headers": self._build_headers(endpoint),
            "timeout": aiohttp.ClientTimeout(total=endpoint.timeout),
            "connector": aiohttp.TCPConnector(limit=100, limit_per_host=30)
        }

    def export_config(self) -> Dict[str, Any]:
        """Exporter la configuration MCP"""
        config = {
            "endpoints": {},
            "validation_status": self.validated_endpoints,
            "last_updated": datetime.now().isoformat()
        }

        for name, endpoint in self.endpoints.items():
            config["endpoints"][name] = {
                "name": endpoint.name,
                "url": endpoint.url,
                "auth_type": endpoint.auth_type,
                "timeout": endpoint.timeout,
                "retry_count": endpoint.retry_count,
                # Note: credentials ne sont pas exportées pour sécurité
                "has_credentials": bool(endpoint.credentials)
            }

        return config

    def load_from_env(self):
        """Charger la configuration depuis les variables d'environnement"""
        # Render MCP
        render_api_key = os.getenv("RENDER_API_KEY")
        if render_api_key:
            self.add_render_endpoint(render_api_key)
            logger.info("Render MCP endpoint configured from environment")

        # Autres endpoints MCP potentiels
        # AWS MCP, Azure MCP, etc.

# Configuration par défaut pour SCRIBE
def create_scribe_mcp_config() -> MCPConfigManager:
    """Créer la configuration MCP pour SCRIBE"""
    config = MCPConfigManager()

    # Charger depuis l'environnement
    config.load_from_env()

    # Validation des configurations requises
    if "render" not in config.endpoints:
        logger.warning(
            "Render API key not found in environment variables. "
            "Set RENDER_API_KEY to enable Render monitoring."
        )

    return config

async def test_mcp_connectivity():
    """Test complet de connectivité MCP"""
    config = create_scribe_mcp_config()

    print("🔧 Testing MCP Connectivity")
    print("=" * 50)

    if not config.endpoints:
        print("❌ No MCP endpoints configured")
        print("💡 Set RENDER_API_KEY environment variable")
        return False

    # Valider tous les endpoints
    results = await config.validate_all_endpoints()

    # Afficher les résultats
    all_valid = True
    for endpoint_name, is_valid in results.items():
        status = "✅" if is_valid else "❌"
        endpoint = config.endpoints[endpoint_name]
        print(f"{status} {endpoint_name}: {endpoint.url}")

        if not is_valid:
            all_valid = False

    print("=" * 50)
    if all_valid:
        print("🎯 All MCP endpoints validated successfully!")
    else:
        print("⚠️  Some MCP endpoints failed validation")

    # Exporter la configuration
    config_export = config.export_config()
    print("\n📋 MCP Configuration:")
    print(json.dumps(config_export, indent=2))

    return all_valid

if __name__ == "__main__":
    asyncio.run(test_mcp_connectivity())