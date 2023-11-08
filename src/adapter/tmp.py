# import asyncio

# from aiohttp import ClientSession

# from src.domain import Settings

# settings = Settings.from_file()

# MODEL = "gpt-3.5-turbo"


# async def send_message(content: str, session: ClientSession) -> None:
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
#     }
#     async with session.post(
#         "https://api.openai.com/v1/chat/completions",
#         headers=headers,
#         json={
#             "model": "gpt-3.5-turbo",
#             "messages": [{"role": "user", "content": content}],
#             "temperature": 0,
#         },
#     ) as resp:
#         response_json = await resp.json()
#         answer = response_json["choices"][0]["message"]["content"]
#         print(answer)
#         # return answer


# async def main() -> None:
#     questions = [
#         "how is the weather today?",
#         "what is water in japanese",
#         "are you doing alright?",
#     ]
#     async with ClientSession() as session:
#         await asyncio.gather(*[send_message(content, session) for content in questions])


# if __name__ == "__main__":
#     asyncio.run(main())
