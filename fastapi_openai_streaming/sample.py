import json
import os
from typing import AsyncGenerator

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

API_KEY = os.environ["OPENAI_API_KEY"]
TIMEOUT = 30

app = FastAPI()


class ResponseMessage(BaseModel):
    content: str


class RequestMessage(BaseModel):
    message: str


async def openai_stream(
    data: dict,
) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            timeout=httpx.Timeout(TIMEOUT),
            headers={
                "Authorization": f"Bearer {API_KEY}",
            },
            json=data,
        ) as response:
            print(f"received response status_code={response.status_code}")
            response.raise_for_status()
            async for chunk in response.aiter_text():
                yield chunk


async def _handle_function_call(name: str, arguments: dict) -> str:
    pass


async def response_generator(message: str) -> AsyncGenerator[str, None]:
    func_call = {"arguments": "", "name": None}
    async for response in openai_stream(
        {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant",
                },
                {"role": "user", "content": message},
            ],
            "model": "gpt-4",
            "stream": True,
        }
    ):
        for block_raw in response.split("\n\n"):
            for line in block_raw.split("\n"):
                if line.startswith("data:"):
                    json_str = line.replace("data:", "").strip()
                    if json_str == "[DONE]":
                        break
                    else:
                        block = json.loads(json_str)

                        # we assume that we only need to look at the first choice
                        choice = block["choices"][0]
                        delta = choice.get("delta")
                    if "function_call" in delta:
                        name = delta["function_call"].get("name")
                        if name:
                            func_call["name"] = name
                        arguments = delta["function_call"].get("arguments")
                        if arguments:
                            func_call["arguments"] += arguments
                    elif "content" in delta:
                        yield ResponseMessage(
                            content=delta["content"],
                        ).model_dump_json() + "\n"

    # we only handle the function call once all the data has been streamed in
    if func_call.get("name"):
        response_message = await _handle_function_call(
            func_call["name"],
            func_call["arguments"],
        )
        yield ResponseMessage(
            content=response_message,
        ).model_dump_json() + "\n"


@app.post("/")
async def message(
    request: RequestMessage,
):
    return StreamingResponse(
        response_generator(request.message),
        media_type="application/x-ndjson",
    )


if __name__ == "__main__":
    uvicorn.run(app)
