import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import fs from "fs";

// Plugin to serve static files BEFORE SPA fallback
function serveStaticFiles() {
  return {
    name: 'serve-static-files',
    configureServer(server) {
      // Insert middleware BEFORE Vite's internal middleware
      return () => {
        server.middlewares.use((req, res, next) => {
          const url = req.url || '';
          
          // Check if it's a request for PDF/CSV/XLSX
          if (/\.(pdf|csv|xlsx)$/i.test(url)) {
            const filePath = path.join(__dirname, 'public', url);
            
            // Check if file exists
            if (fs.existsSync(filePath)) {
              // Set correct content type
              if (url.endsWith('.pdf')) {
                res.setHeader('Content-Type', 'application/pdf');
              } else if (url.endsWith('.csv')) {
                res.setHeader('Content-Type', 'text/csv');
              } else if (url.endsWith('.xlsx')) {
                res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
              }
              
              // Prevent caching
              res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
              res.setHeader('Pragma', 'no-cache');
              res.setHeader('Expires', '0');
              
              // Serve the file
              const fileStream = fs.createReadStream(filePath);
              fileStream.pipe(res);
              return; // Don't call next() - we're handling this request
            }
          }
          
          next();
        });
      };
    }
  };
}

export default defineConfig({
  plugins: [react(), serveStaticFiles()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    open: true,
    fs: {
      strict: false,
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    minify: "terser",
  },
  publicDir: 'public',
});
