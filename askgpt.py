import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import openai
from rich.console import Console
from rich.markdown import Markdown

frozenclass = dataclass(frozen=True, slots=True, unsafe_hash=True)

console = Console()

GPT3_MODEL = "gpt-3.5-turbo"
GPT4_MODEL = "gpt-4"
DEFAULT_MODEL = GPT3_MODEL


@frozenclass
class Message:
    role: str
    content: str


@frozenclass
class Choice:
    index: int
    message: Message
    finish_reason: str


@frozenclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@frozenclass
class Response:
    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]
    usage: Usage | None = None


def read_env(filename: str = ".env") -> dict:
    file = Path(__file__).parent / filename
    if not file.exists():
        raise Exception(f"{filename} not found")

    def parse(val: str):
        if val[0] in {'"', "'"}:  # Removing quotes if they exist
            if val[0] == val[-1]:
                value = val[1:-1]
            else:
                raise ValueError(f"{val} inproperly quoted")

        # Type casting
        if val.isdecimal():
            value = int(val)  # Integer type
        elif val.lower() in {"true", "false"}:
            value = val.lower() == "true"  # Boolean type
        else:
            if val[0].isdecimal():  # Float type
                try:
                    value = float(val)
                except ValueError as ve:
                    pass
                else:
                    return value
            value = val  # Otherwise, string type
        return value

    config = {}
    ln = 1

    with file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    key, value = line.split("=", 1)
                    config[key.strip()] = parse(value.strip())
                except ValueError as ve:
                    raise Exception(f"Invalid env line number {ln}: {line}") from ve
            ln += 1
    return config


def programming_prompt():
    return """
    You are a professional computer scientist who are expert on multiple programming language, 
    including python, cpp, java. in the our upcoming conversion, i want you to help me with your expertise;
    please note that, whenever i ask questions related to these programming language, answer me with this context:
    python version of 3.10, cpp version of cpp20, java version of java 18

    {question}
    """


async def ask_async(question, model, stream=True):
    msgs = [{"role": "user", "content": question}]
    cache = ""

    console.rule("[bold red]Answer")

    stream_resp = await openai.ChatCompletion.acreate(
        model=model, stream=stream, messages=msgs
    )

    async for resp in stream_resp:  # type: ignore
        for choice in resp.choices:
            content = choice.get("delta", {}).get("content")
            if content:
                cache += content
                console.print(content, end="")
    return cache


def ask_question(question: str, context: list, model: str, stream=True):
    current_question = dict(role="user", content=question)
    context.append(current_question)

    try:
        chat_resp = openai.ChatCompletion.create(
            model=model, stream=stream, messages=context
        )
    except Exception as e:
        raise e
    else:
        console.print("question sent to openai")

    console.rule("[bold red]Answer")
    console.print("")

    answer = ""
    for resp in chat_resp:
        for choice in resp.choices:  # type: ignore
            content = choice.get("delta", {}).get("content")
            if content:
                answer += content
                console.print(content, end="")
        resp_model = Response(**resp)
    return answer


def save_answer(question: str, answer: str):
    answer_path = Path("answer.md")
    question_banner = f"""\n==============================\nQuestion({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n{question}\n"""

    answer_banner = """\nAnswer:\n"""

    with open(answer_path, "a") as f:
        f.write(question_banner)
        f.write(answer_banner)
        f.write(answer)
        f.write("\n==============================\n")


def show_answer(answer_file: str = "answer.md"):
    answer_md = Path(__file__).parent / answer_file
    console.print(Markdown(answer_md.read_text()))


def quit(context: list):
    question, answer = "", ""
    if context:
        for msg in context:
            role = msg.get("role")
            if not role:
                continue
            if role == "user":
                question = msg.get("content")
            elif role == "assistant":
                answer = msg.get("content")

            save_answer(question, answer)

    console.rule("[bold red]Answer")
    console.print("\nBye!")


async def interactive_mode(namespace: argparse.Namespace):
    while True:
        question = console.input("\nQuestion: ")

        if question == "q" or question == "quit":
            quit(context)
            return

        try:
            answer = ask_question(question, context=context, model=model)
        except KeyboardInterrupt as ke:
            quit(context)
            return

        history = dict(role="assistant", content=answer)
        context.append(history)


async def main():
    config_file = "src/.env"
    openai.api_key = read_env(config_file)["OPENAI_API_KEY"]
    context = list()

    parser = argparse.ArgumentParser(description="cli for chatgpt")
    parser.add_argument(
        "question",
        default="",
        nargs="?",
        type=str,
        help="the question you would like to ask",
    )
    parser.add_argument("--gpt4", help="use the gpt4 model", action="store_true")
    parser.add_argument("--show", help="show the answer", action="store_true")
    args = parser.parse_args()

    if args.gpt4:
        model = GPT4_MODEL
    else:
        model = GPT3_MODEL

    question = args.question

    if not question:
        await interactive_mode(args)
    else:
        answer = ask_question(question, context, model=model)
        save_answer(question, answer)
        if args.show:
            show_answer()

    quit(context)


if __name__ == "__main__":
    asyncio.run(main())
