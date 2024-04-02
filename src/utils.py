
import logging
import os

import openai


def get_gpt_response(
        messages,
        temperature=0,
        stream=False,
):
    logging.info("Getting gpt response ...")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        temperature=temperature,
        stream=stream
    )
    logging.info(f"GPT response: {response}")
    try:
        output = response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error getting gpt response: {e}")
        output = ""
    return output
