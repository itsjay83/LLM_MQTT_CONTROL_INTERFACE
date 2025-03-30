from langchain_openai import ChatOpenAI
# from langchain.schema import HumanMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler
import json
import paho.mqtt.client as mqtt

from langchain_core.prompts import FewShotChatMessagePromptTemplate, ChatPromptTemplate

from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

# LLM 초기화 (예: GPT-3.5-turbo 사용)
llm = ChatOpenAI(
    api_key=API_KEY,
    model="gpt-4o",
		streaming=True,
		callbacks=[
			StreamingStdOutCallbackHandler(),
		]
)

examples = [
    {
        "question" : "왼쪽으로 40도 돌려줘",
        "answer" : """
				{
					"mode": "relative",
					"angle": (number),
					"direction": "cw" 또는 "ccw",
					"action": "blink_led" 또는 "none"
				}
				"""
		},
    {
        "question" : "0도부터 180도까지 30도씩 돌려줘. 매번 LED를 켜",
        "answer" : """
				{
					"mode": "absolute",
					"from": (number),
					"to": (number),
					"step": (number),
					"direction": "cw" 또는 "ccw",
					"action": "blink_led" 또는 "none"
				}
				"""
		},
]

example_prompt = ChatPromptTemplate.from_messages(
	[
		("human", "{question}"),
		("ai", "{answer}")
	]
)

example_prompts = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

final_prompt = ChatPromptTemplate.from_messages([
	("system", """
		너는 IoT 제어 명령어를 분석해서 제공된 JSON 포맷 중 하나로 변환해야 해.
		'```json```' 은(는) 없이 출력해줘
	"""),
	example_prompts,
	("human", "{question}")
])

chain = final_prompt | llm

def parse_to_plan(question):

    result = chain.invoke({
		"question" : question
		})

    response = result.content
    return json.loads(response)

# 초기 변수 설정
broker = "broker.hivemq.com"
topic = "ljsllmmqtt/json"

# MQTT 클라이언트 초기화 및 연결 (broker: hivemq.com)
client = mqtt.Client()
client.connect(broker, 1883)

# 사용자 입력 받아서 파싱 후 MQTT로 전송
user_input = input("명령어를 입력하세요: ")
plan = parse_to_plan(user_input)

client.publish(topic, json.dumps(plan))
print("계획 전송 완료:", plan)
client.disconnect()
