from dotenv import load_dotenv
from openai import OpenAI

class Review_ChatBot:
    def __init__(self, model, system_message="You are a helpful assistant."):
        load_dotenv()
        self.client = OpenAI()
        self.messages = []
        self.model = model
        self.add_message("system", system_message)

    def add_message(self, role, content):
        
        self.messages.append(
            {
                "role" : role,
                "content" : content
            }
        )

    def get_response(self, user_input):
    
        self.add_message("user", user_input)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            
        )
        
        response = completion.choices[0].message.content
        self.add_message("assistant", response)
    
        return response
       

    def reset(self):
        self.messages = self.messages[:1]

    

    def get_review_comment(self, my_text, their_reply):
        """
        1) my_text: 내가 쓴 글
        2) their_reply: 내 글에 대한 어떤 사람(혹은 AI)의 답변
        - 리턴: their_reply에 대한 챗봇의 새로운 댓글
        """
        prompt = (
            f"아래는 내가 쓴 글이야:\n"
            f"---\n{my_text}\n---\n\n"
            f"그리고 이 글에 대한 답변이 있어:\n"
            f"---\n{their_reply}\n---\n\n"
            f"위 내용을 바탕으로, 해당 답변에 대한 너의 코멘트(리뷰/피드백/추가 의견 등)를 작성해줘."
        )

        return self.get_response(prompt)