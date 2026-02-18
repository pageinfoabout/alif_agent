

import os
import aiohttp
import asyncio

from dotenv import load_dotenv
from livekit.agents import llm

import logging
import json


logger = logging.getLogger("tools")
load_dotenv()

# Глобальный lkapi (один на все tools)
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")


async def get_token() -> str:
    url = "https://crmexchange.1denta.ru/api/v2/auth"
    payload = {
        "email": "YOUR_EMAIL",
        "password": "YOUR_PASSWORD"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            raw = await response.text()
            print("=== AUTH API RESPONSE ===")
            print("Status:", response.status)
            if response.status != 200:
                raise Exception(f"Auth failed: {raw}")
            data = await response.json()
            return data["token"] 
    




@llm.function_tool
async def delete_booking(visit_id) -> str:
    """
    Возвращает список врачей с доступными слотами времени
    за указанный период по выбранной услуге.
    """
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjU1MjksImFwaUtleSI6InRuTUU1OHVNbXVZQjBUS01FN3JDIiwib3JnSWQiOjEwNDg0LCJuYW1lIjoi0KPQvNCw0YDQsdC10LrQvtCyINCa0LDQvdCw0YLQsdC10Log0KPQvNCw0YDQsdC10LrQvtCy0LjRhyIsInBob25lIjoiKzcoOTk5KTg1MS02Ni05MiIsImVtYWlsIjoiYWxpZmRlbnRtb3Njb3dAZ21haWwuY29tIiwiaWF0IjoxNzcxMjQ1MzA3fQ.ftZ3FNzSEiOuS6Ex9I_kcpCsGmL_Z7ElGAp5P62fMFs"
    }

    url = f"https://crmexchange.1denta.ru/api/v2/visit/{visit_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers,) as response:
            raw = await response.text()
            # 🔍 PRINT RAW RESPONSE (always)
            print("=== get_date API RESPONSE ===")
            print("Status:", response.status)
            print("Body:", raw)
            print("============================")

            # ✅ 200 OK
            if response.status == 200:
                return raw

            # ❌ errors: 404 / 422 / others
            try:
                error = json.loads(raw)
            except json.JSONDecodeError:
                error = {"code": "UNKNOWN_ERROR", "message": raw}

            return json.dumps(
                {
                    "http_status": response.status,
                    "code": error.get("code"),
                    "message": error.get("message")
                },
                ensure_ascii=False
            )
        



@llm.function_tool
async def get_date(from_date: str, to_date: str, doc_id: int) -> str:
    """
    Возвращает список доступных дат у конкретного врача
    """

    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjU1MjksImFwaUtleSI6InRuTUU1OHVNbXVZQjBUS01FN3JDIiwib3JnSWQiOjEwNDg0LCJuYW1lIjoi0KPQvNCw0YDQsdC10LrQvtCyINCa0LDQvdCw0YLQsdC10Log0KPQvNCw0YDQsdC10LrQvtCy0LjRhyIsInBob25lIjoiKzcoOTk5KTg1MS02Ni05MiIsImVtYWlsIjoiYWxpZmRlbnRtb3Njb3dAZ21haWwuY29tIiwiaWF0IjoxNzcxMjQ1MzA3fQ.ftZ3FNzSEiOuS6Ex9I_kcpCsGmL_Z7ElGAp5P62fMFs"
    }

    params = {
        "serviceIds[]": "515",
        "from": from_date,
        "to": to_date
    }

    url = f"https://crmexchange.1denta.ru/api/v2/resource/{doc_id}/date"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:

            raw = await response.text()

            # 🔍 PRINT RAW RESPONSE (always)
            print("=== get_date API RESPONSE ===")
            print("Status:", response.status)
            print("Body:", raw)
            print("============================")

            # ✅ 200 OK
            if response.status == 200:
                return raw

            # ❌ errors: 404 / 422 / others
            try:
                error = json.loads(raw)
            except json.JSONDecodeError:
                error = {"code": "UNKNOWN_ERROR", "message": raw}

            return json.dumps(
                {
                    "http_status": response.status,
                    "code": error.get("code"),
                    "message": error.get("message")
                },
                ensure_ascii=False
            )
        

@llm.function_tool
async def get_time(date: str, doc_id: int) -> str:
    """
    Возвращает список врачей с доступными слотами времени
    за указанный период по выбранной услуге.
    """


    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjU1MjksImFwaUtleSI6InRuTUU1OHVNbXVZQjBUS01FN3JDIiwib3JnSWQiOjEwNDg0LCJuYW1lIjoi0KPQvNCw0YDQsdC10LrQvtCyINCa0LDQvdCw0YLQsdC10Log0KPQvNCw0YDQsdC10LrQvtCy0LjRhyIsInBob25lIjoiKzcoOTk5KTg1MS02Ni05MiIsImVtYWlsIjoiYWxpZmRlbnRtb3Njb3dAZ21haWwuY29tIiwiaWF0IjoxNzcxMjQ1MzA3fQ.ftZ3FNzSEiOuS6Ex9I_kcpCsGmL_Z7ElGAp5P62fMFs"
    }

    params = {
        "serviceIds[]": "515",
        "date": date
    }
    url = f"https://crmexchange.1denta.ru/api/v2/resource/{doc_id}/time"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:

            raw = await response.text()

            # 🔍 PRINT RAW RESPONSE (always)
            print("=== get_date API RESPONSE ===")
            print("Status:", response.status)
            print("Body:", raw)
            print("============================")

            # ✅ 200 OK
            if response.status == 200:
                return raw

            # ❌ errors: 404 / 422 / others
            try:
                error = json.loads(raw)
            except json.JSONDecodeError:
                error = {"code": "UNKNOWN_ERROR", "message": raw}

            return json.dumps(
                {
                    "http_status": response.status,
                    "code": error.get("code"),
                    "message": error.get("message")
                },
                ensure_ascii=False
            )
    

@llm.function_tool
async def get_services() -> str:
    """
    Возвращает список услуг которые предоставляет поликлиника


    :return: Список услуг в формате JSON
    id = номер услуги
    title = это название услуги 
    price = это цена услуги

    :example:
    [
        {
            "id": "130",
            "title": "Наложение лечебной повязки при заболеваниях слизистой оболочки полости рта и пародонта в области одного зуба при обработке пародонтального кармана диодным лазером",
            "description": null,
            "category": "Профилактика заболеваний полости рта",
            "durationSeconds": 0,
            "price": {
                "currencyCode": "RUB",
                "range": [
                    "450.00",
                    "450.00"
                ]
            }
        }
    ]
       """
   
   
    url = "https://crmexchange.1denta.ru/api/v2/service"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjU1MjksImFwaUtleSI6InRuTUU1OHVNbXVZQjBUS01FN3JDIiwib3JnSWQiOjEwNDg0LCJuYW1lIjoi0KPQvNCw0YDQsdC10LrQvtCyINCa0LDQvdCw0YLQsdC10Log0KPQvNCw0YDQsdC10LrQvtCy0LjRhyIsInBob25lIjoiKzcoOTk5KTg1MS02Ni05MiIsImVtYWlsIjoiYWxpZmRlbnRtb3Njb3dAZ21haWwuY29tIiwiaWF0IjoxNzcxMjQ1MzA3fQ.ftZ3FNzSEiOuS6Ex9I_kcpCsGmL_Z7ElGAp5P62fMFs"
    }
    params = {
        "page": 2,
        "perPage": 460
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                print(f"вот ответ", data)
                return json.dumps(data, ensure_ascii=False)
            
               
            else:
                return json.dumps(
                    {"error": f"HTTP {response.status}"},
                    ensure_ascii=False
                )





@llm.function_tool
async def get_doctors() -> str:
    url = "https://crmexchange.1denta.ru/api/v2/resource"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjU1MjksImFwaUtleSI6InRuTUU1OHVNbXVZQjBUS01FN3JDIiwib3JnSWQiOjEwNDg0LCJuYW1lIjoi0KPQvNCw0YDQsdC10LrQvtCyINCa0LDQvdCw0YLQsdC10Log0KPQvNCw0YDQsdC10LrQvtCy0LjRhyIsInBob25lIjoiKzcoOTk5KTg1MS02Ni05MiIsImVtYWlsIjoiYWxpZmRlbnRtb3Njb3dAZ21haWwuY29tIiwiaWF0IjoxNzcxMjQ1MzA3fQ.ftZ3FNzSEiOuS6Ex9I_kcpCsGmL_Z7ElGAp5P62fMFs"
    }
    params = {
        "page": 2,
        "perPage": 460
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"вот ответ", data)
                return json.dumps(data, ensure_ascii=False)
            
               
            else:
                return json.dumps(
                    {"error": f"HTTP {response.status}"},
                    ensure_ascii=False
                )




            
    


    



    






