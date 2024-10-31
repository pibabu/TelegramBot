import asyncio
import telegram


async def main():
    bot = telegram.Bot("Telegram_API_Key")
    async with bot:
        print(await bot.get_me())


if __name__ == '__main__':
    asyncio.run(main())