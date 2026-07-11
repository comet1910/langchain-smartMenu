"""
agent助手代码
"""


from pathlib import Path

from langchain.tools import tool

import psycopg2
from psycopg2.extras import RealDictCursor
import os

from dotenv import load_dotenv
load_dotenv()

root_path = Path(__file__).parent.parent
embeddings = None
milvus_client = None

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


async def create_agent():

    from pathlib import Path
    from langchain.agents import create_agent
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI()
    with open(str(root_path / 'agent'/'prompts'/'system_prompts.txt')) as f:
        system_prompt = f.read()

    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[]
    )


if __name__ == '__main__':
    res = user_flavor_search.invoke({"user_query":"清淡的食物"})
    print(res)

