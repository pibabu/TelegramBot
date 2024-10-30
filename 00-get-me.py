import asyncio
import telegram


async def main():
    bot = telegram.Bot("xxxxxxx")
    async with bot:
        print(await bot.get_me())


if __name__ == '__main__':
    asyncio.run(main())