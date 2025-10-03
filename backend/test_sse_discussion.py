#!/usr/bin/env python3
"""
Test script for SSE AutoGen Discussion Streaming
Phase 2.2 - Validation du streaming des messages Plume & Mimir
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_sse_discussion_stream():
    """
    Test SSE streaming endpoint with AutoGen discussion
    """

    print("🧪 Test SSE Discussion Streaming - Phase 2.2")
    print("=" * 60)

    # Test configuration
    BASE_URL = "http://localhost:8000"
    ENDPOINT = f"{BASE_URL}/api/v1/chat/orchestrated/stream"

    # Test cases
    test_cases = [
        {
            "name": "Discussion explicite (Plume et Mimir mentionnés)",
            "payload": {
                "message": "Plume et Mimir, pouvez-vous discuter ensemble sur l'importance de la documentation technique ?",
                "mode": "auto",
                "session_id": f"test_session_{int(datetime.now().timestamp())}"
            }
        },
        {
            "name": "Routing prénom Plume seul",
            "payload": {
                "message": "Plume, peux-tu reformuler cette phrase : 'Python est un langage de programmation' ?",
                "mode": "auto",
                "session_id": f"test_session_{int(datetime.now().timestamp())}"
            }
        },
        {
            "name": "Routing prénom Mimir seul",
            "payload": {
                "message": "Mimir, trouve mes notes sur la programmation Python",
                "mode": "auto",
                "session_id": f"test_session_{int(datetime.now().timestamp())}"
            }
        },
        {
            "name": "Mode discussion forcé",
            "payload": {
                "message": "Qu'est-ce que RAG en intelligence artificielle ?",
                "mode": "discussion",
                "session_id": f"test_session_{int(datetime.now().timestamp())}"
            }
        }
    ]

    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{len(test_cases)}: {test_case['name']}")
        print("-" * 60)

        await run_sse_test(ENDPOINT, test_case['payload'])

        if i < len(test_cases):
            print("\n⏳ Pause de 2s avant le test suivant...")
            await asyncio.sleep(2)

    print("\n" + "=" * 60)
    print("✅ Tests terminés")


async def run_sse_test(endpoint: str, payload: dict):
    """
    Run single SSE streaming test
    """

    events_received = {
        'start': 0,
        'processing': 0,
        'agent_message': 0,
        'complete': 0,
        'error': 0,
        'keepalive': 0
    }

    agent_messages = []

    print(f"📤 Payload: {json.dumps(payload, ensure_ascii=False)[:100]}...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream('POST', endpoint, json=payload) as response:

                if response.status_code != 200:
                    print(f"❌ Erreur HTTP: {response.status_code}")
                    return

                print(f"✅ Connexion SSE établie (status: {response.status_code})")
                print("\n📨 Événements SSE reçus:\n")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            print("✓ [DONE] - Stream terminé")
                            break

                        try:
                            event = json.loads(data_str)
                            event_type = event.get('type', 'unknown')

                            # Count events
                            if event_type in events_received:
                                events_received[event_type] += 1

                            # Display event
                            if event_type == 'start':
                                print(f"  ▶ START - session_id: {event.get('session_id')}")

                            elif event_type == 'processing':
                                status = event.get('status', 'unknown')
                                node = event.get('node', 'unknown')
                                print(f"  ⚙️  PROCESSING - {node}: {status}")

                            elif event_type == 'agent_message':
                                agent = event.get('agent', 'unknown')
                                message = event.get('message', '')
                                to = event.get('to', '')

                                # Truncate long messages
                                message_preview = message[:80] + "..." if len(message) > 80 else message

                                agent_messages.append({
                                    'agent': agent,
                                    'to': to,
                                    'message': message
                                })

                                emoji = "🖋️" if agent == "plume" else "🧠"
                                print(f"  {emoji}  {agent.upper()} → {to}: {message_preview}")

                            elif event_type == 'complete':
                                result = event.get('result', {})
                                print(f"  ✅ COMPLETE")
                                print(f"     - Agent: {result.get('agent_used')}")
                                print(f"     - Agents involved: {result.get('agents_involved')}")
                                print(f"     - Processing time: {result.get('processing_time_ms')}ms")
                                print(f"     - Tokens used: {result.get('tokens_used')}")
                                print(f"     - Discussion messages: {len(result.get('discussion_history', []))}")

                            elif event_type == 'error':
                                error = event.get('error', 'Unknown error')
                                print(f"  ❌ ERROR: {error}")

                            elif event_type == 'keepalive':
                                print(f"  💓 KEEPALIVE")

                        except json.JSONDecodeError as e:
                            print(f"  ⚠️  JSON decode error: {e}")
                            print(f"     Raw data: {data_str[:100]}...")

        # Summary
        print(f"\n📊 Résumé des événements:")
        for event_type, count in events_received.items():
            if count > 0:
                print(f"   - {event_type}: {count}")

        if agent_messages:
            print(f"\n💬 Messages agents capturés: {len(agent_messages)}")
            for msg in agent_messages:
                print(f"   - {msg['agent']} → {msg['to']}: {msg['message'][:60]}...")

    except httpx.TimeoutException:
        print("❌ Timeout - Le serveur n'a pas répondu à temps")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")


if __name__ == "__main__":
    print("\n🚀 Démarrage des tests SSE AutoGen Discussion\n")

    try:
        asyncio.run(test_sse_discussion_stream())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {str(e)}")
