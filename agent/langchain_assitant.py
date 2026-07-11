"""
agent助手代码
"""


from pathlib import Path

from langchain.tools import tool

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pydantic import BaseModel,Field

from dotenv import load_dotenv
load_dotenv()

root_path = Path(__file__).parent.parent
embeddings = None
milvus_client = None
engine = None
agent = None

#创建连接池
def postgres_connection():
    global engine
    if engine is None:
        from sqlalchemy import create_engine
        engine = create_engine(
            url = f"postgresql+psycopg2://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DATABASE', 'postgres')}",
            pool_size=15
        )
    return engine

@tool
def search_main_dishes():
    """
    搜索餐厅中的主菜
    """
    key_name_mapping = {
        "dish_name":"主菜名称",
        "price":"价格",
        "description":"描述",
        "category":"分类",
        "spice_level":"辣度等级",
        "flavor":"口味",
        "main_ingredients":"主要食材",
        "cooking_method":"烹饪方法",
        "is_vegetarian":"是否为素食",
        "allergens":"过敏信息"
    }

    with psycopg2.connect(host=os.getenv("POSTGRES_HOST"),
                          port=int(os.getenv("POSTGRES_PORT", 5432)),
                          user=os.getenv("POSTGRES_USERNAME"),
                          password=os.getenv("POSTGRES_PASSWORD"),
                          dbname=os.getenv("POSTGRES_DATABASE", "postgres"),
                          ) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            sql = """
            select
                dish_name,
                price,
                description,
                category,
                spice_level,
                flavor,
                main_ingredients,
                cooking_method,
                is_vegetarian,
                allergens
            from 
                menu_items
            where
                is_featured = true

            """
            cursor.execute(sql)
            results = cursor.fetchall()
           
            #将数据封装成json
            json_results = []
            for item in results:
                json_item = {}
                for key,value in item.items():
                    json_item[key_name_mapping[key]] = value
                json_results.append(json_item)
            
            return json_results


def get_embeddings():
    global embeddings
    if embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model= str(root_path / "models"/"bge-m3"))
    return embeddings

def get_milvus_client():
    global milvus_client
    if milvus_client is None:
        from pymilvus import MilvusClient
        milvus_client = MilvusClient(
            uri=os.getenv("MILVUS_URI"),
            token=os.getenv("MILVUS_TOKEN")
        )
    return milvus_client



#查找菜品工具
@tool
def user_flavor_search(user_query:str):
    """
    基于用户口味，查找相关的菜品
    """
    #1、构建用户query的向量,使用本地的bge-m3
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(user_query)

    #2、连接milvus ，进行向量检索
    client = get_milvus_client()

    #3、进行向量检索
    search_res = client.search(
        collection_name="menu_items",
        data = [query_vector],
        anns_field="vector",
        output_fields=["text"],
        limit = 3
    )

    #4、解析搜索结果
    if search_res:
        all_results = search_res[0]

        final_result = []

        for item in all_results:
            item_str = item["entity"]["text"]
            final_result.append(item_str)

        return final_result
    else:
        return "在当前库中没有符合用户喜好的菜品"

class ReservationToolArgsInfo(BaseModel):
    num_people:int = Field(description="就餐人数")
    num_children:int = Field(description="预约的0-2岁儿童人数")
    arrival_time:str = Field(description="到达时间，格式为YYYY-MM-DD HH:MM")
    seat_preference:str = Field(description="座位偏好，没有时为空字符串")
    main_dish_preference:str = Field(description="主菜偏好，没有时为空字符串")
    comment:str = Field(description="备注，没有时为空字符串")



#预定工具
@tool(args_schema=ReservationToolArgsInfo)
def make_reservation(num_people:int,num_children:int,arrival_time:str,seat_preference:str,main_dish_preference:str,comment:str):
    """
    用来进行餐厅预订的工具
    向数据库写入数据
    """
    from sqlalchemy import text
    engine = postgres_connection()
    with engine.connect() as conn:
       sql = """
         INSERT INTO reservation_order(num_people, num_children, arrival_time, seat_preference, main_dish_preference, other_comments)
         VALUES (:num_people, :num_children, :arrival_time, :seat_preference, :main_dish_preference, :other_comments)
       """
       param_dict = {
           "num_people":num_people,
           "num_children":num_children,
           "arrival_time":arrival_time,
           "seat_preference":seat_preference,
           "main_dish_preference":main_dish_preference,
           "other_comments":comment
       }
       conn.execute(statement = text(sql),parameters=param_dict)
       conn.commit()
       return "预约成功"


async def create_agent():
    global agent
    if agent is  None:
        from pathlib import Path
        from langchain.agents import create_agent
        from langchain_openai import ChatOpenAI
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langgraph.checkpoint.memory import InMemorySaver
        # from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        import sqlite3

        checkpointer = InMemorySaver()



        # client = MultiServerMCPClient(
        #     connections={
        #         "amap-mpas":{
        #             "transport":"sse",
        #             "url":"http://localhost:83000/v1/chat/completions"
        #         }
        #     }
        # )

        llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "deepseek-v4-flash"),
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
        )
        with open(str(root_path / 'agent'/'prompts'/'system_prompt.txt'),encoding="utf-8",mode="r") as f:
            system_prompt = f.read()

        # mcp_tools = await client.get_tools()

        agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            # tools=[make_reservation,user_flavor_search,search_main_dishes]+mcp_tools,
            #未使用mcp的tools
            tools=[make_reservation,user_flavor_search,search_main_dishes],
            checkpointer=checkpointer
        )
    return agent

async def test_agent():
    agent = await create_agent()
    config = {"configurable":{"thread_id":"123"}}
    res = agent.invoke({"messages":[{"role":"user","content":"你能帮我做什么"}]}, config=config)
    print(res["messages"][-1].content)

if __name__ == '__main__':
    # res = make_reservation.invoke({"num_people":4,"num_children":2,"arrival_time":"2023-12-12 18:00","seat_preference":"","main_dish_preference":"","comment":""})
    # print(res)
    import asyncio
    asyncio.run(test_agent())

