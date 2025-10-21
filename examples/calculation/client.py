import asyncio

from dp.agent.client import MCPClient


async def main():
    client = MCPClient("http://127.0.0.1:8000/sse")
    try:
        await client.connect_to_server()
        result = await client.call_tool(
            "run_dp_train",
            arguments={
                "training_data": "local:///path/to/training_data",
            },
        )
        results = result.content[0].text
        print("results", results)
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
