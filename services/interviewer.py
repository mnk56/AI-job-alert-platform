import os
from google import genai
from google.genai import types

MODEL = 'gemini-3.6-flash'

def _client():
    return genai.Client(api_key=os.environ['GOOGLE_API_KEY'])
def build_system_promt(company):
    return f"""あなたは「{company.name}」の面接官です。 
以下がこの会社の経営理念・特徴です:
{company.description}
この会社の理念に基づいて、応募者に質問してください。
- 1回の発言で質問は1つだけにしてください
- 応募者の回答に対してリアクションしてから次の質問に進んでください
- 会社の理念や特徴に関連する質問を中心にしてください
"""
def build_contents(session):
    contents = []
    for log in session.chatlogs.all():
        role = 'model' if log.role == 'interviewer' else 'user'
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=log.message)])
        )
    return contents

def generate_reply(session):
    client = _client()
    response = client.models.generate_content(
        model=MODEL,
        contents=build_contents(session),
        config=types.GenerateContentConfig(
            system_instruction=build_system_promt(session.company),
        ),
    )
    return response.text