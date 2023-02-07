import openai

openai.api_key = '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'


async def summ_text(text):
    return text
    # resp = await openai.Completion.create(
    #     model="text-davinci-003",  # curie-001
    #     prompt=text2 + '\n\nTl;dr',
    #     temperature=0.3,
    #     max_tokens=24,
    #     top_p=1.0,
    #     frequency_penalty=0.0,
    #     presence_penalty=1
    # )
