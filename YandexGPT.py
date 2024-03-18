# Позволяет вести диалог с Yandex GPT

import json
import requests

YANDEX_GPT_API_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/'
YANDEX_GPT_API_KEY = 'INSERT_YOUR_API_KEY_FROM_YANDEX_ACCOUNT'
YANDEX_GPT_API_FOLDER_ID = 'INSERT_YOUR_FOLDER_ID_FROM_YANDEX_ACCOUNT'
RESPONSE_STRIP_CHARS = '«»„““”"❝❞„⹂〝〞〟＂‹›❮❯‚‘‘‛’❛❜❟`\'., '


class YandexGPT:
    """YandexGPT completion assistant"""

    def __init__(
            self,
            api_url: str,  # YandexGPT API
            api_key: str,  # YandexGPT API-Key
            api_folder_id: str,  # YandexGPT API folder ID
            system_prompt: str = ' ',  # Role
            chars_strip: str = '',  # Chars to be removed from the edges of YandexGPT responses
            model: str = 'yandexgpt/latest',  # model
            temperature: float = 0.6,  # default is 0.6, [0.0..1.0]
            max_tokens: int = 2000,  # default 2000
            is_stream: bool = False,
    ) -> None:
        self._api_ulr = api_url
        self._api_key = api_key
        self._api_folder_id = api_folder_id
        self._chars_strip = chars_strip
        self._messages = [
            {
                'role': "system",
                'text': system_prompt,
            },
        ]
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._is_stream = is_stream

    def get_answer(self, message: str, **replace_texts) -> str:
        """Get text response from YandexGPT by prompt"""

        # Replacing all special keywords to text in message
        for replace_keyword, replace_text in replace_texts.items():
            message.replace(replace_keyword, replace_text)

        # Add user message
        self._messages.append({"role": "user", "text": message})

        headers = {
            'Content-Type': "text/event-stream" if self._is_stream else "application/json",
            'Authorization': f"Api-Key {self._api_key}",
        }

        data = {
            'modelUri': f"gpt://{self._api_folder_id}/{self._model}",
            'completionOptions': {
                'max_tokens': self._max_tokens,
                'temperature': self._temperature,
                'stream': self._is_stream,
            },
            'messages': self._messages,
        }
        # Get response from YandexGPT
        try:
            response = requests.post(self._api_ulr + 'completion', headers=headers, stream=self._is_stream, json=data)
            response.encoding = 'utf-8'
        except Exception as e:
            yield [f"[Error!!! YandexGPT something wrong: {str(e)}]"]
            return

        if response.status_code == 200 and response.text:
            if self._is_stream:
                text = ''
                for token in response.iter_lines(decode_unicode=True, delimiter='\n'):
                    if token:
                        token_data = json.loads(token)
                        yield str(token_data['result']['alternatives'][0]['message']['text'])[len(text):]
                        text = str(token_data['result']['alternatives'][0]['message']['text'])
            else:
                response_data = response.json()
                text = response_data['result']['alternatives'][0]['message']['text'].strip(self._chars_strip)
                yield text
        else:
            print(f"Error accessing YandexGPT, request code: {response.status_code}")
            return

        # Remember YandexGPT response
        self._messages.append({"role": "assistant", "text": text})


if __name__ == "__main__":
    yandex_gpt = YandexGPT(
        api_url=YANDEX_GPT_API_URL,
        api_key=YANDEX_GPT_API_KEY,
        api_folder_id=YANDEX_GPT_API_FOLDER_ID,
        chars_strip=RESPONSE_STRIP_CHARS,
    )
    print("Starting dialog with YandexGPT:\n")

    step = 1
    while True:
        print(f"{step:2}. You:", end="\n    ")
        question = input("What do you want to ask YandexGPT: ")
        if not question:
            break

        answer = yandex_gpt.get_answer(question)
        print(f"{step:2}. YandexGPT:", end="\n    ")
        for chunk in answer:
            print(chunk, end="")
        print()

        print('_' * 100, end='\n\n')
        step += 1
