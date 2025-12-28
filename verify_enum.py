#!/usr/bin/env python
"""验证enum值"""
import asyncio
from app.core.database import engine
import sqlalchemy as sa

async def check_enum():
    async with engine.begin() as conn:
        result = await conn.execute(sa.text("SELECT unnest(enum_range(NULL::recurrencetype))"))
        print('Current recurrencetype enum values:')
        for row in result:
            print(f'  - {row[0]}')

asyncio.run(check_enum())
