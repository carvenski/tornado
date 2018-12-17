
# ab -n 10000 -c 10000 http://0.0.0.0/3000/

import asyncio
from sanic import Sanic
from sanic.response import json

app = Sanic()

@app.route("/")
async def test(request):
    await asyncio.sleep(5)
    return json({"blog": " xiaorui.cc "})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

# use sanic replace tornado in python3.6 ?

