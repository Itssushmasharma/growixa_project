/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    config.optimization.minimize = false;
    return config;
  },
  reactStrictMode: true,
};

export default nextConfig;
