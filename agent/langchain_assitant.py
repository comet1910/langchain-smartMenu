"""
agent助手代码
"""
import json
from multiprocessing import Value

from langchain.tools import tool
import pymysql
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
load_dotenv()



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



async def create_agent():

    from pathlib import Path
    from langchain.agents import create_agent
    from langchain_openai import ChatOpenAI
    root_path = Path(__file__).parent.parent
    llm = ChatOpenAI()
    with open(str(root_path / 'agent'/'prompts'/'system_prompts.txt')) as f:
        system_prompt = f.read()

    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[]
    )


if __name__ == '__main__':
    res = search_main_dishes.invoke({})
    print(res)

