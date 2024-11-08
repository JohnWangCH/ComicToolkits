import os
from ollama_prompt_helper import OllamaPromptHelper
import asyncio

OLLAMA_INSTRUCTION_FILE_NAME = "ollama_instruction.txt"


def extract_prompt(text):
    xxx = text.split("**Negative Prompt:**", 1)
    prompt = (
        xxx[0]
        .replace("**Negative Prompt:**", "")
        .replace("**Prompt:**", "")
        .replace("Prompt:", "")
        .replace("\n", "")
        .strip()
    )
    negative_prompt = (
        xxx[1]
        .replace("**Negative Prompt:**", "")
        .replace("Negative", "")
        .replace("Prompt:", "")
        .replace("**Prompt:**", "")
        .replace("\n", "")
        .strip()
    )

    return prompt, negative_prompt


async def _get_instruction(file_name, file_path: str = ""):
    with open(
        os.path.join(file_path, file_name),
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


async def generate_prompt(content: str, prev_context: list[int]):

    # Use ollama
    instruction = await _get_instruction(file_name=OLLAMA_INSTRUCTION_FILE_NAME)
    print(instruction)
    ollama_prompt_helper = OllamaPromptHelper(instruction=instruction)
    prompt, ollama_context = await ollama_prompt_helper.ollama_generate_prompt(
        prompt=content, keep_context=True, context=prev_context
    )
    print(prompt)
    # output to files


if __name__ == "__main__":
    print("Test prompt gen")
    asyncio.run(
        generate_prompt(
            content="面对韩雷的质问,楚韩芯一时沉默,旋即绝美的面庞上升起了一抹坚决道,小雷,你是分支唯一的希望,",
            prev_context=[],
        )
    )
    # generate_prompt()
