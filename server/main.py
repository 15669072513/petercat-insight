from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router  # 假设你的路由模块在这里

app = FastAPI()

# 添加 CORS 中间件

cors_origins = (
    ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers="*",
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,
                host="0.0.0.0",
                port=8001,
                ssl_certfile="/usr/local/openresty/nginx/conf/certs/mosn-chain-2024.crt",
                ssl_keyfile="/usr/local/openresty/nginx/conf/certs/mosn-2024.key")
