import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

// next.config.js
// module.exports = {
//     output: 'export',
// };

// next.config.js
module.exports = {
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:8000/api/:path*', // 代理到 FastAPI
            },
        ];
    },
};


export default nextConfig;
