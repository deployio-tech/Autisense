const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const dotenv = require("dotenv");
const fs = require("fs");
const path = require("path");

// Load environment variables
dotenv.config();

// Import routes
const authRoutes = require("./routes/authRoutes");
const childRoutes = require("./routes/childRoutes");
const screeningRoutes = require("./routes/screeningRoutes");
const centersRoutes = require("./routes/centersRoutes");
const chatRoutes = require("./routes/chatRoutes");

const app = express();

const parseOrigins = (value, fallback) => {
  const origins = String(value || "")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);

  return origins.length > 0 ? origins : fallback;
};

const defaultDevOrigins = [
  "http://localhost:3000",
  "http://localhost:5173",
  "http://127.0.0.1:5173",
];

const defaultProdOrigins = [
  "https://autisense.deployio.tech",
  "https://autisense-ml.deployio.tech",
  "https://autisense-rag.deployio.tech",
  "https://autisense-emotion.deployio.tech",
];

const corsOrigins = process.env.CORS_ORIGINS
  ? parseOrigins(process.env.CORS_ORIGINS, defaultDevOrigins)
  : process.env.NODE_ENV === "production"
    ? defaultProdOrigins
    : defaultDevOrigins;

// Middleware
app.use(
  cors({
    origin: corsOrigins,
    credentials: true,
  }),
);
app.use(express.json({ limit: "50mb" })); // Increase limit for video frames
app.use(express.urlencoded({ extended: true, limit: "50mb" }));

// Static files for uploads
app.use("/uploads", express.static("uploads"));

const frontendBuildDir = path.join(__dirname, "public");
const frontendIndexFile = path.join(frontendBuildDir, "index.html");
const hasFrontendBuild = fs.existsSync(frontendIndexFile);

if (hasFrontendBuild) {
  app.use(express.static(frontendBuildDir));
}

// API Routes
app.use("/api/auth", authRoutes);
app.use("/api/children", childRoutes);
app.use("/api/screenings", screeningRoutes);
app.use("/api/centers", centersRoutes);
app.use("/api/chat", chatRoutes);
app.use("/api/video", require("./routes/videoProcessingRoutes"));

if (hasFrontendBuild) {
  app.get("*", (req, res, next) => {
    if (
      req.path.startsWith("/api") ||
      req.path.startsWith("/uploads") ||
      req.path === "/health"
    ) {
      return next();
    }

    if (req.method === "GET" && req.accepts("html")) {
      return res.sendFile(frontendIndexFile);
    }

    return next();
  });
}

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "OK", timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || "Internal Server Error",
    ...(process.env.NODE_ENV === "development" && { stack: err.stack }),
  });
});

// Database connection
mongoose
  .connect(process.env.MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
  })
  .then(() => {
    console.log("✅ Connected to MongoDB");

    // Start server
    const PORT = process.env.PORT || 5000;
    const server = app.listen(PORT, "0.0.0.0", () => {
      console.log(`🚀 Server running on http://localhost:${PORT}`);
      console.log(`📊 Environment: ${process.env.NODE_ENV}`);
      console.log(`🌐 Ready to accept connections`);
    });

    // Set server timeouts for long video processing
    server.timeout = 900000; // 15 minutes
    server.keepAliveTimeout = 900000; // 15 minutes
    server.headersTimeout = 910000; // Slightly longer than keepAliveTimeout

    server.on("error", (error) => {
      if (error.code === "EADDRINUSE") {
        console.error(`❌ Port ${PORT} is already in use`);
        process.exit(1);
      } else {
        console.error("❌ Server error:", error);
        process.exit(1);
      }
    });
  })
  .catch((err) => {
    console.error("❌ MongoDB connection error:", err);
    process.exit(1);
  });

// Handle unhandled promise rejections
process.on("unhandledRejection", (err) => {
  console.error("Unhandled Promise Rejection:", err);
  process.exit(1);
});
