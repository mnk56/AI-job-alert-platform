import json
from . import interviewer
from google.genai import types

JUDGE_INSTRUCTION = """これまでの面接のやり取りを踏まえ、応募者を評価してください。
    次のキーだけを持つ JSON を出力してください:
    "score": 1〜5 の整数(5が最高)
    "passed": true または false
    "comment": 100文字以内の講評(日本語)
"""

def parse_judgment(text):
    """Gemini の応答をパースし、検証して dict を返す。読み取れなければ None。"""
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        data = json.loads(text[start:end])

        score = int(data['score'])

        if not (1 <= score <= 5):
            raise ValueError(f'スコアが範囲外: {score}')

        passed_raw = data['passed']
        passed = (
            passed_raw if isinstance(passed_raw, bool)
            else str(passed_raw).lower() == 'true'
        )

        return {
            'score': score,
            'passed': passed,
            'comment': str(data.get('comment', ''))[:100],
        }

    except (ValueError, KeyError, json.JSONDecodeError):
        return None

def evaluate(session):
    """セッションの全履歴をもとに、AIによる最終評価を取得する。"""
    client = interviewer._client()
    contents = interviewer.build_contents(session)
    
    if not contents:
        return None

    # Google GenAI-ийн Content объект эсвэл dict-ээс сүүлийн 'model' байвал хасах
    while contents and (
        getattr(contents[-1], 'role', None) == 'model' or 
        (isinstance(contents[-1], dict) and contents[-1].get('role') == 'model')
    ):
        contents.pop()

    # Хэрэв challenger (user) ямар ч хариулт өгөөгүй хоосон үлдсэн бол
    if not contents:
        return {
            'score': 1,
            'passed': False,
            'comment': '回答がありませんでした。',
        }


    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="以上で面接を終了します。これまでの回答を総合的に評価し、合否とスコアを判定してください。")]
        )
    )

    response = client.models.generate_content(
        model=interviewer.MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_INSTRUCTION,
            response_mime_type='application/json',
        ),
    )
    return parse_judgment(response.text)
    