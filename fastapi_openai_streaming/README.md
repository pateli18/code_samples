# FastAPI OpenAI Streaming

A small example illustrating streaming the OpenAI api output with your FastAPI application

## Setup

```
pip install -r requirements.txt
```

## Testing

Run the following to start your server (be sure to put in your actual OPENAI_API_KEY):

```
OPENAI_API_KEY=... python3 sample.py
```

Run the following curl command in a separate process:

```
curl -X POST -H "Content-Type: application/json" -d '{"message":"what is the capital of the united states?"}' http://localhost:8000
```
