import asyncio
import json
import os
import random
from pprint import pprint

import aiohttp

role_enabled = False


class OllamaPromptHelper:
    _base_url = "http://127.0.0.1:11434"
    _model = "llama3.1"
    _saved_context = None

    # TODO: change the character_prompts with role profiles when role_enable is True
    _character_prompts = """
    ## Character appearances
    -  君逍遙 : A handsome man with black long hair and blue eyes, wearing white clothes
    -  姜柔 : A beautiful woman with black long hair and red eyes, wearing red clothes
    """

    _gen_prompt_instruction_disable_role = """
    Act as prompt generator, I will give you text and you reply the prompt to describe an image that matches that text in details, answer with one response only.
    
    ## About the prompt
    - The prompts will only include common vocabulary and avoid any specialized or specific terms mentioned in the text. 
    - Prompts should include the main subject, location, actions of the main subject, and lighting. However, the prompt you output should not be divided into sections, just split them with a comma .
    - Main Subject: Provide a brief English description of the main subject of the image. This should include a summary of the core content, which could be a person, event, object, or scene. This part should be generated based on the theme I provide each time. You can add more reasonable details related to the theme. 
       1. If the subject is a person,  just reply a simple term such as "1girl," "1man," "1 group of people," "an elder man/woman." 
       2. If it's purely a scene, w/o a specific person or event, just reply "no human".
    - Location: Typically choose "outdoor" or "indoor," but more detailed descriptions are also possible. Use common vocabulary to describe the location, such as "indoor," "outdoor," "underwater," "outer space," "woods," "seashore," "palace," etc. Avoid using specialized terms from novels.
    - Main Subject Actions: If the main subject is a living being (including people or animals), you must specify what action the subject is performing.
    - Lighting: The overall lighting effect of the image, e.g., "cinematic lighting," "glowing," "studio lighting."
    - Shot type: Choose one of the following formats based on the image's requirements: "close-up," "portrait," "landscape" (use "landscape" if there are no characters).
    
    ## Note
    - If I input in Chinese to communicate with you, but it is crucial that your response is in English.
    - The response should include prompt only.
    - The response should be less than 50 words.
    
    """

    default_simple_prompt = """Act as prompt generator, I will give you text and you should create a brief, straightforward caption to describe an image that matches that text in details, suitable for a text-to-image AI system. Focus on the main elements, key characters, and overall scene without elaborate details. Provide a clear and concise description in one or two sentences."""

    def __init__(self, instruction):
        if role_enabled:
            self.gen_prompt_instruction = f"{instruction}\n\n{self._character_prompts}"
        else:
            self.gen_prompt_instruction = f"{self._gen_prompt_instruction_disable_role}"

    async def _send_request(
        self,
        model: str,
        prompt: str,
        context: list[int],
        options: any,
        keep_alive: str,
        system: str,
    ):
        url = f"{self._base_url}/api/generate"

        # Request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "options": options,
            "context": context,
            "keep_alive": keep_alive,
            "stream": False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response_json = await response.json()
                return response_json

    async def ollama_separate_scenes(self, prompt):
        return await self._ollama_generate_advance(
            prompt=prompt,
            system=self.separate_scenes_instruction,
            keep_context=True,
        )

    async def ollama_generate_prompt(self, prompt, keep_context, context):

        return await self._ollama_generate_advance(
            prompt=prompt,
            system=self.gen_prompt_instruction,
            keep_context=keep_context,
            context=context,
        )

    async def _ollama_generate_advance(
        self,
        prompt,
        system,
        debug=False,
        url=_base_url,
        top_k=40,
        top_p=0.9,
        temperature=0.8,
        num_predict=-1,
        tfs_z=1.00,
        keep_alive=600,
        keep_context=False,
        context=None,
        seed=None,
    ):
        if seed is None:
            seed = random.randint(1, 2**31)
        options = {
            "seed": seed,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "num_predict": num_predict,
            "tfs_z": tfs_z,
        }

        if context is not None and isinstance(context, str):
            string_list = context.split(",")
            context = [int(item.strip()) for item in string_list]

        if keep_context and context is None:
            context = self._saved_context

        if debug:
            print(
                f"""[Ollama Generate Advance] 
                request query params:
                - prompt: {prompt}
                - url: {url}
                - model: {self._model}
                - options: {options}
                """
            )
        response = await self._send_request(
            model=self._model,
            prompt=prompt,
            context=context,
            options=options,
            keep_alive=str(keep_alive) + "m",
            system=system,
        )
        if debug:
            print("[Ollama Generate Advance]\nResponse:\n")
            pprint(response)

        if keep_context:
            self._saved_context = response["context"]

        return (
            response["response"],
            response["context"],
        )


async def test():
    context = """「李總，您的電話，是全通公司曾總。」
秘書小玉一直不明白自己公司的李強總經理，如此精明的人為什麼喜歡和這個曾總混在一起，這個全通公司是一家標準的空殼公司，而公司老總曾偉光絕對是混世魔王，心裡嘆息一聲又想：「老總的事，不是我們小職員可以問的。」搖搖頭又忙自己的工作去了。
總經理的為人公司上下都很佩服，他憑著闖勁，一個人以極少的資金創辦這家貿易公司，從一無所有到擁有這家上千萬資產的公司，只用了短短的六年時間，在商界雖然有很多人嫉妒，但是也不得不佩服他有魄力，眼光獨到，敢想敢干。
李強今年二十九歲，個頭矮小，皮膚黝黑。他自小家境貧寒，憑著過人的聰明和朋友的資助，磕磕絆絆的上完四年大學。由於天生喜交友，人又仗義豪爽，因此結交許多朋友。
「喂，偉光啊，有什麼事，一會兒我還要開會……什麼？有事要見面談……算了吧，哪天不能說？明天我請你吃飯再說，今天……不行啊，什麼……擔保的事，靠……好吧，我馬上來！」李強臉色鐵青地放下電話，愣了愣神說道：「小玉，下午的會議取消，你通知彭子東和劍仔到希爾頓酒店四零三房間去，要快！」
李強心急如火的開車來到希爾頓酒店，下車後急急忙忙地衝上樓去，曾偉光已經等在門口了。看見李強來了，他說：「強哥，你別急，這事要從長計議……」
「安升公司是怎麼回事？」
「唉，他們公司的老總涉嫌詐騙，卷了大筆財產逃了，幾家給他擔保的公司都急得團團轉，被騙的公司已經告上法院，我先告訴一聲，免得你措手不及。」又道：「當初，我也看走眼了，唉！強哥，都是我不好，不該勸你去擔保他們公司。」
「現在不是道歉的時候，事情還沒搞清楚。」李強已經冷靜下來，小眼睛透出精明的光，問道：「什麼時候的事情？」
曾偉光對李強的冷靜很吃驚，道：「大概有三天了吧，我剛知道就打電話給你了。」"""

    res = await OllamaPromptHelper(
        instruction=OllamaPromptHelper.separate_scenes_instruction
    ).ollama_separate_scenes(prompt=context)
    output = res[0]
    print("This is the json format response (before correction):\n")
    # print(output)
    # output = output.replace(",\n'", "',").replace('"', "")

    # print("This is the json format response (after correction):\n")
    # print(output)

    # scenes = output.split('","')
    json_object = json.loads(output)

    print("This is the json format response:\n")
    # pprint(scenes)
    pprint(json_object)

    for list in json_object:
        print(context[list[0] : list[1]])
    # pprint(json_object[0])


if __name__ == "__main__":
    print("Test prompt gen")
    asyncio.run(test())
