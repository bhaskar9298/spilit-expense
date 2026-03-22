import asyncio
from db.init import setup_collection_hybrid

async def main():
    await setup_collection_hybrid()

if __name__ == "__main__":
    asyncio.run(main())