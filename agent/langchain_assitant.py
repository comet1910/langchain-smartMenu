"""
agent助手代码
"""
from langchain.tools import tool
import pymysql
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

@tool
def search_main_dishes_mysql():
    """
    搜索餐厅中的主菜（MySQL版本）
    """

    with pymysql.connect(host=os.getenv("MYSQL_HOST"),
                        port=int(os.getenv("MYSQL_PORT", 3306)),
                        user=os.getenv("MYSQL_USER"),
                        passwd=os.getenv("MYSQL_PASSWORD"),
                      ) as conn:
        with conn.cursor() as cursor:
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
                smart_menu.menu_items
            where
                is_featured =1 

            """
            cursor.execute(sql)
            results = cursor.fetchall()
            return results


@tool
def search_main_dishes():
    """
    搜索餐厅中的主菜
    """

    with psycopg2.connect(host=os.getenv("POSTGRES_HOST"),
                          port=int(os.getenv("POSTGRES_PORT", 5432)),
                          user=os.getenv("POSTGRES_USERNAME"),
                          password=os.getenv("POSTGRES_PASSWORD"),
                          dbname=os.getenv("POSTGRES_DATABASE", "postgres"),
                          ) as conn:
        with conn.cursor() as cursor:
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
            return results



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

