import re
from openai import OpenAI
from dotenv import load_dotenv
import os

import json

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def generate_estimate(fermi_problem: str):
    """
    Get the estimation

    Args:
    fermi problem (str): The Fermi Problem to be solved

    Returns:
    int: The estimated final value of the Fermi Problem
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"I will prompt you with a Fermi Problem. You are to approach it through the following steps: 1. Outline the steps needed for a Fermi Estimation of the answer. 2. Proceed with actioning the first step, keeping text to a minimum, then provide the outcome of the step. 3. Repeat the stepwise procedure until all of the steps have been completed. 4. Report your final answer at the end in the format 'FINAL ANSWER: ____'. You are to provide the answer as solely a number in Standard Notation without any commas, symbols, or units",
            },
            {"role": "user", "content": [{"type": "text", "text": fermi_problem}]},
        ],
        temperature=1,
        max_tokens=1650,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    # get the number value in the "FINAL ANSWER: X" string
    response_text = response.choices[0].message.content
    if response_text == None or "FINAL ANSWER: " not in response_text:
        raise ValueError("The response did not contain the final answer")

    response_text = response_text.split("FINAL ANSWER: ")[1]

    try:
        # Remove commas and convert to integer
        number_str_clean = response_text.replace(",", "").replace(" ", "").split(".")[0]
        return int(number_str_clean)
    except ValueError:
        raise ValueError(f"Could not convert {response_text} to an integer")


def generate_fermi_problem():
    """
    Get a Fermi Problem

    Returns:
    str: The Fermi Problem
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": 'You are a magical carnival machine called "Guess That Value!". You generate unique Fermi Problems focusing on a wide range of topics that are creative and whimsical. When you receive the instruction "Go", you return ONLY a Fermi Problem without any preamble or introductory phrases. Make sure to keep the Fermi Problem concise and to the point and avoid cliche or overused problems.',
            },
            {"role": "user", "content": [{"type": "text", "text": "Go"}]},
        ],
        temperature=1.09,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    return response.choices[0].message.content
