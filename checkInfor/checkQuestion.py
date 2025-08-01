import openai
from Utilis.utilis import img2base64
from Doubao.prompts_conf import system_prompt
import asyncio
from asyncio import Semaphore, gather
model = "qwen3-32b"
api_key = "sk-85caf631866d4b0fb79eaeeb34f8f96e"
url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

class QALabeler:
    def __init__(self, api_key=api_key, model=model, url= url,activate_stream=True,parallel_core=10,
                 question_key="question", answer_key="answer", system_prompt=system_prompt
                 
                 ):
        self.clinet = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=url if url else None
        )
        self.question_key = question_key
        self.answer_key = answer_key
        self.model = model
        self.activate_stream = activate_stream
        self.parallel_core = parallel_core
        self.system_prompt = system_prompt
    def run_check(self,QA_file,use_img = False):
        import pandas as pd
        if QA_file.endswith('.xlsx'):
            data = pd.read_excel(QA_file)
        elif QA_file.endswith('.csv'):
            data = pd.read_csv(QA_file)
        elif QA_file.endswith('.json'):
            data = pd.read_json(QA_file)
        semaphore = Semaphore(self.parallel_core)
        async def get_tasks():
            tasks = []
            for index in range(0,len(data),self.parallel_core):
                batch = data.iloc[index:index+self.parallel_core]
                task_batch = []
                for _, row in batch.iterrows():
                    question = row[self.question_key]
                    answer = row[self.answer_key]
                    img_path = row.get("image_path", None) if use_img else None
                    task_batch.append(self.get_questions_label({
                        "question": question,
                        "answer": answer,
                        "image_path": img_path
                    }))
                async with semaphore:
                    tasks.extend(await gather(*task_batch))
            return tasks
        labels = asyncio.run(get_tasks())
            
        
        
        # Save the results to a new CSV file
        data['label'] = labels
        data["label"].map(lambda x: "模型回答正确" if x == 1 else "模型无法回答", na_action='ignore')
        data.to_csv(QA_file.replace('.csv', '_labeled.csv'), index=False)
        
    async def get_questions_label(self,QA):
    
        question,answer = QA["question"],QA["answer"]
        img_path = QA["image_path"]
        img_url = img2base64(img_path) if img_path else None
        
        get_answer = await self.get_response(question,answer,img_url)
        label = await self.check_answer(question,answer,get_answer)
        return label
    async def get_response(self, question, answer, img_url=None):
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": self.system_prompt}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"请回答以下问题,返回内容直接给出答案，不需要给出思考过程：{question} \n\n "},
                                    ]
            }
        ]
        response = await self.clinet.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=4096,
            top_p=0.7,
            stream=self.activate_stream
        )
        if self.activate_stream:
            reasoning_content = ""
            answer_content = ""
            async for chunk in response:
                if not chunk.choices:
                    print("\nUsage:")
                    print(chunk.usage)
                else:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                        reasoning_content += delta.reasoning_content
                    else:
                        answer_content += delta.content
            return answer_content
        else:
            content = response.choices[0].message.content
            #reasoning_content = response.choices[0].message.reasoning_content
            return content
    async def check_answer(self,question, answer, get_answer,show_question_answer=True):
        input_prompt = f"""这是问题和答案\n\n Question: {question}\nAnswer: {answer} \n\n
        这是模型回答的答案:{get_answer}
        请判断给模型回答的答案是否正确
        如果问题是简答题目，回答答案要求内容完整且正确，涵盖问题的所有要点。且不可以出现错误的内容或者与答案冲突的内容
        如果正确请返回1,如果不正确请返回0 
        返回内容只能是数字"""
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": self.system_prompt}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": input_prompt}
                ]
            }
        ]
        
        
        response = await self.clinet.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=4096,
            top_p=0.7,
            stream=self.activate_stream
        )
        print("="*15)
        print(f"input_prompt: {input_prompt}")
        
        if self.activate_stream:
            label_content = ""
            async for chunk in response:
                if not chunk.choices:
                    print("\nUsage:")
                    
                    print(chunk.usage)
                else:
                    delta = chunk.choices[0].delta
                    
                    print(delta.content, end='\n\n', flush=True)
                    label_content += delta.content
            return int(label_content.strip())
        else:
            content = response.choices[0].message.content
    
            print(content)
            return int(content.strip())

if __name__ =="__main__":
    file_path = "/Users/Shared/VLReasoningTCL/data/bookoutput/book_checked/merged_data_qa_page30-41.csv"
    qa_labeler = QALabeler(activate_stream=False,parallel_core=10)
    qa_labeler.run_check(file_path,use_img=False)
    