/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    // Disable Webpack JS minification to prevent SWC native worker crash (0xC0000409) on Windows
    config.optimization.minimize = false;
    return config;
  },
  reactStrictMode: true,
};

export default nextConfig;
