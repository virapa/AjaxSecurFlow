import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'imagesvc.prod.ajax.systems',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;
