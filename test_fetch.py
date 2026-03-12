import asyncio
from utils.request_manager import RequestManager

async def test():

    async with RequestManager() as rm:

        html = await rm.fetch("https://www.goodfirms.co/directory/software-development-companies")

        print(len(html))

asyncio.run(test())